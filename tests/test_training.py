from pathlib import Path

from musbot.env.acciones import AccionLegal, AccionMus
from musbot.training.benchmark import benchmark_trainers
from musbot.training.catalog import best_model_run, list_model_runs
from musbot.training.evaluate import evaluate
from musbot.training.experiment_manager import TrainingRunManager
from musbot.training.registry import list_trainer_definitions
from musbot.training.self_play import expandir_acciones_para_agente
from musbot.training.train import train
from tests._tmp_utils import workspace_tmp_dir


def test_training_crea_run_con_checkpoints_metricas_y_resumen() -> None:
    with workspace_tmp_dir() as tmp_path:
        root_dir = tmp_path / "modelos"

        resultado = train(
            root_dir=root_dir,
            episodes_to_run=2,
            checkpoint_interval=1,
            evaluation_interval=1,
            evaluation_hands=2,
            seed=7,
            notes="run de prueba",
        )

        manager = TrainingRunManager(root_dir=root_dir)
        paths, config, state = manager.load_run(resultado.run_id)

        assert resultado.run_dir == paths.run_dir
        assert state.total_episodes == 2
        assert state.latest_checkpoint is not None
        assert state.best_checkpoint is not None
        assert paths.config_path.is_file()
        assert paths.state_path.is_file()
        assert paths.metrics_path.is_file()
        assert paths.summary_path.is_file()
        assert paths.latest_checkpoint_path.is_file()
        assert paths.best_checkpoint_path.is_file()
        assert (paths.run_dir / "comportamiento_mixed.md").is_file()
        assert (paths.run_dir / "comportamiento.md").is_file()
        assert "run de prueba" in paths.summary_path.read_text(encoding="utf-8")
        assert config.episodes_to_run == 2
        assert config.trainer_version == "tabular_v1"
        assert len(manager.read_metrics(paths)) == 2


def test_training_permire_resume_y_fork() -> None:
    with workspace_tmp_dir() as tmp_path:
        root_dir = tmp_path / "modelos"

        inicial = train(
            root_dir=root_dir,
            episodes_to_run=2,
            checkpoint_interval=1,
            evaluation_interval=1,
            evaluation_hands=2,
            seed=11,
        )

        resumido = train(
            root_dir=root_dir,
            resume_run_id=inicial.run_id,
            episodes_to_run=1,
            checkpoint_interval=1,
            evaluation_interval=1,
            evaluation_hands=2,
            seed=12,
        )

        manager = TrainingRunManager(root_dir=root_dir)
        _, _, estado_resumido = manager.load_run(resumido.run_id)
        assert estado_resumido.total_episodes == 3

        bifurcado = train(
            root_dir=root_dir,
            fork_from_run_id=inicial.run_id,
            fork_checkpoint="best",
            episodes_to_run=1,
            checkpoint_interval=1,
            evaluation_interval=1,
            evaluation_hands=2,
            seed=13,
        )

        assert bifurcado.run_id != inicial.run_id
        paths_bifurcado, _, estado_bifurcado = manager.load_run(bifurcado.run_id)
        assert estado_bifurcado.parent_run_id == inicial.run_id
        assert Path(paths_bifurcado.summary_path).is_file()


def test_evaluate_carga_un_run_entrenado() -> None:
    with workspace_tmp_dir() as tmp_path:
        root_dir = tmp_path / "modelos"

        resultado = train(
            root_dir=root_dir,
            episodes_to_run=1,
            checkpoint_interval=1,
            evaluation_interval=1,
            evaluation_hands=2,
            seed=21,
        )

        evaluacion = evaluate(
            run_id=resultado.run_id,
            root_dir=root_dir,
            checkpoint="latest",
            episodes=2,
        )

        assert evaluacion.run_id == resultado.run_id
        assert 0.0 <= evaluacion.win_rate <= 1.0
        assert evaluacion.behavior_report_paths


def test_evaluate_permire_cambiar_baseline_rival() -> None:
    with workspace_tmp_dir() as tmp_path:
        root_dir = tmp_path / "modelos"

        resultado = train(
            root_dir=root_dir,
            episodes_to_run=1,
            checkpoint_interval=1,
            evaluation_interval=1,
            evaluation_hands=2,
            seed=22,
            opponent="mixed",
        )

        evaluacion = evaluate(
            run_id=resultado.run_id,
            root_dir=root_dir,
            checkpoint="latest",
            episodes=2,
            opponent="heuristic",
        )

        assert evaluacion.run_id == resultado.run_id
        assert 0.0 <= evaluacion.win_rate <= 1.0


def test_catalogo_y_registro_de_trainers() -> None:
    definitions = list_trainer_definitions()
    assert any(definition.trainer_version == "tabular_v1" for definition in definitions)
    assert any(definition.trainer_version == "tabular_v2" for definition in definitions)
    assert any(definition.trainer_version == "tabular_v3" for definition in definitions)
    assert any(definition.trainer_version == "tabular_v4" for definition in definitions)
    assert any(definition.trainer_version == "tabular_v5" for definition in definitions)

    with workspace_tmp_dir() as tmp_path:
        root_dir = tmp_path / "modelos"

        train(
            root_dir=root_dir,
            episodes_to_run=1,
            checkpoint_interval=1,
            evaluation_interval=1,
            evaluation_hands=2,
            seed=31,
            notes="primer run",
            trainer_version="tabular_v1",
        )
        train(
            root_dir=root_dir,
            episodes_to_run=2,
            checkpoint_interval=1,
            evaluation_interval=1,
            evaluation_hands=2,
            seed=32,
            notes="segundo run",
            trainer_version="tabular_v1",
        )

        runs = list_model_runs(root_dir=root_dir)
        assert len(runs) == 2
        assert all(run.trainer_version == "tabular_v1" for run in runs)

        mejor = best_model_run(root_dir=root_dir, trainer_version="tabular_v1")
        assert mejor is not None
        assert mejor.run_id in {run.run_id for run in runs}


def test_training_v5_decae_epsilon_y_registra_metricas() -> None:
    with workspace_tmp_dir() as tmp_path:
        root_dir = tmp_path / "modelos"

        resultado = train(
            root_dir=root_dir,
            episodes_to_run=20,
            checkpoint_interval=5,
            evaluation_interval=5,
            evaluation_hands=2,
            seed=51,
            epsilon=1.0,
            trainer_version="tabular_v5",
            patience=0,  # desactiva early stopping para este test
        )

        manager = TrainingRunManager(root_dir=root_dir)
        paths, config, state = manager.load_run(resultado.run_id)
        metricas = manager.read_metrics(paths)

        assert config.trainer_version == "tabular_v5"
        assert state.total_episodes == 20
        # epsilon arranca en 1.0 y decae 0.995 por episodio -> debe bajar.
        assert metricas[-1]["epsilon"] < 1.0
        assert metricas[-1]["epsilon"] < metricas[0]["epsilon"]
        assert "states_visited" in metricas[-1]


def test_training_early_stopping_para_en_plateau() -> None:
    with workspace_tmp_dir() as tmp_path:
        root_dir = tmp_path / "modelos"

        # patience pequeña: si no mejora en 2 evaluaciones consecutivas, para.
        resultado = train(
            root_dir=root_dir,
            episodes_to_run=200,
            checkpoint_interval=5,
            evaluation_interval=5,
            evaluation_hands=2,
            seed=61,
            trainer_version="tabular_v5",
            patience=10,
        )

        manager = TrainingRunManager(root_dir=root_dir)
        _, _, state = manager.load_run(resultado.run_id)
        # Con patience=10 debería parar bastante antes de los 200 episodios.
        assert state.total_episodes < 200


def test_expandir_acciones_para_agente_materializa_envites() -> None:
    acciones = expandir_acciones_para_agente(
        [
            AccionMus.PASAR,
            AccionLegal.envidar(cantidad_minima=2),
            AccionMus.ORDAGO,
        ]
    )

    assert AccionLegal.simple(AccionMus.PASAR) in acciones
    assert AccionLegal.simple(AccionMus.ORDAGO) in acciones
    assert AccionLegal.envidar(2) in acciones
    assert AccionLegal.envidar(5) in acciones
    assert all(
        accion.tipo is not AccionMus.ENVIDAR or accion.cantidad is not None for accion in acciones
    )


def test_training_mixed_y_heuristic_quedan_operativos() -> None:
    with workspace_tmp_dir() as tmp_path:
        root_dir = tmp_path / "modelos"

        resultado = train(
            root_dir=root_dir,
            episodes_to_run=2,
            checkpoint_interval=1,
            evaluation_interval=1,
            evaluation_hands=2,
            seed=41,
            opponent="heuristic",
            trainer_version="tabular_v2",
        )

        manager = TrainingRunManager(root_dir=root_dir)
        _, config, state = manager.load_run(resultado.run_id)
        assert config.opponent == "heuristic"
        assert state.total_episodes == 2


def test_benchmark_trainers_devuelve_registros() -> None:
    with workspace_tmp_dir() as tmp_path:
        root_dir = tmp_path / "modelos"

        resumen = benchmark_trainers(
            trainer_versions=("tabular_v1", "tabular_v2", "tabular_v3", "tabular_v4"),
            seeds=(0,),
            root_dir=root_dir,
            training_opponent="mixed",
            evaluation_opponents=("random",),
            episodes_to_run=1,
            checkpoint_interval=1,
            evaluation_interval=1,
            evaluation_hands=1,
        )

        assert len(resumen.records) == 4
        assert {record.trainer_version for record in resumen.records} == {
            "tabular_v1",
            "tabular_v2",
            "tabular_v3",
            "tabular_v4",
        }
        agregado = resumen.aggregate()
        assert ("tabular_v1", "random") in agregado
        assert ("tabular_v2", "random") in agregado
        assert ("tabular_v3", "random") in agregado
        assert ("tabular_v4", "random") in agregado
