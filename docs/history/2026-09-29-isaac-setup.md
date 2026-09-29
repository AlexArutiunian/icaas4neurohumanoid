# 2026-09-29 — Isaac Sim / Isaac Lab setup

## Цель

Подготовить локальную среду на ноутбуке с RTX 3080 Ti для разработки симуляции Unitree G1 и сохранить совместимость с сервером RTX 5090, где Isaac Sim / Isaac Lab уже установлены администратором.

## Проверено до установки

| Компонент | Состояние |
|---|---|
| GPU | NVIDIA GeForce RTX 3080 Ti Laptop, 16 GB VRAM |
| NVIDIA Driver | `580.178.04` |
| `nvidia-smi` CUDA capability | `13.0` |
| ОС | Ubuntu 22.04.5 LTS |
| glibc | `2.35` |
| системный Python | `3.10.12` |
| Conda | изначально отсутствовала |

Системный Python решено не изменять: Isaac/Unitree устанавливаются в отдельное окружение.

## Серверный baseline

По предоставленной инструкции серверный стек подготовлен на Isaac Sim `5.1.0` и Isaac Lab; удалённый GUI запускается через WebRTC поверх ZeroTier. Серверное администраторское окружение не изменяем без необходимости.

## Принятые решения

1. Для ноутбука использовать официальный `unitreerobotics/unitree_sim_isaaclab`, а не собирать G1 вручную поверх чистого Isaac Sim.
2. Использовать Isaac Sim `5.1`, чтобы локальная среда соответствовала серверному baseline.
3. Установку вести через официальный `auto_setup_env.sh` Unitree в отдельное окружение `unitree_sim_env`.
4. Показание `CUDA 13.0` в `nvidia-smi` не использовать как версию Python/CUDA-окружения: зависимости Isaac/PyTorch остаются изолированными.
5. Тяжёлые прогоны и обучение планировать на RTX 5090; локальную RTX 3080 Ti использовать для GUI, сцены и отладки.

## Ход установки

Запущено:

```bash
chmod +x auto_setup_env.sh
bash auto_setup_env.sh 5.1 unitree_sim_env
```

### 1. Assets

Официальные Unitree assets скачаны и распакованы успешно (`assets.zip`, около 1.2 GB).

### 2. CycloneDDS

CycloneDDS собран и установлен в `~/cyclonedds/install`.

### 3. Conda

Первый запуск Phase 3 остановился из-за отсутствия команды `conda`. После установки/инициализации Miniconda setup дошёл до создания окружения `unitree_sim_env`, но Conda потребовала принять Terms of Service для стандартных Anaconda channels:

```text
CondaToSNonInteractiveError: Terms of Service have not been accepted
```

Требуется принять ToS для:

```text
https://repo.anaconda.com/pkgs/main
https://repo.anaconda.com/pkgs/r
```

Статус: **blocked on Conda channel ToS acceptance**. Isaac Sim и Isaac Lab локально ещё не установлены.

## Следующий шаг

Принять ToS, затем повторно запустить тот же setup script:

```bash
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r

cd ~/unitree_sim_isaaclab
bash auto_setup_env.sh 5.1 unitree_sim_env
```

Повторный запуск оставляем штатным: уже скачанные assets и собранный CycloneDDS повторно использоваться там, где это поддерживает скрипт.

После завершения установки проверить:

```bash
conda activate unitree_sim_env
python --version
python -c "import torch; print(torch.__version__, torch.cuda.is_available(), torch.cuda.get_device_name(0))"
isaacsim
```

После успешного старта Isaac Sim — проверить официальный G1 + Inspire task и затем переходить к сцене сортировщика.
