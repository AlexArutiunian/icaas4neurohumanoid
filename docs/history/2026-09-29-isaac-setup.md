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
| Conda | установлена позже через Miniconda |

Системный Python не изменяем: Isaac/Unitree устанавливаются в отдельное окружение.

## Серверный baseline

По предоставленной инструкции серверный стек подготовлен на Isaac Sim `5.1.0` и Isaac Lab; удалённый GUI запускается через WebRTC поверх ZeroTier. Серверное администраторское окружение не изменяем без необходимости.

## Принятые решения

1. Использовать официальный `unitreerobotics/unitree_sim_isaaclab`, а не собирать G1 вручную поверх чистого Isaac Sim.
2. Использовать Isaac Sim `5.1`, чтобы локальная среда соответствовала серверному baseline.
3. Держать всё в отдельном `unitree_sim_env`.
4. Для Isaac Sim 5.1 зафиксировать совместимый Isaac Lab commit `80094be3245aa5c8376a7464d29cb4412ea518f5`, указанный в официальной инструкции Unitree.
5. RTX 3080 Ti использовать для GUI/сцены/отладки; тяжёлые прогоны и обучение — на RTX 5090.

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

Сначала отсутствовала команда `conda`, затем Miniconda была установлена и инициализирована. Отдельно были приняты Terms of Service стандартных Anaconda channels.

### 4. Isaac Sim / Isaac Lab

Окружение `unitree_sim_env` создано на Python `3.11.16`. Setup дошёл до установки Isaac Lab, но завершился ошибкой зависимостей:

```text
isaaclab==32.0.0 depends on Python>=3.12
current Python: 3.11.16
```

Перед ошибкой `isaaclab.sh` успел заменить целевые `torch 2.7.0 + cu126` на `torch 2.12.0 + cu130` и обновить NumPy.

Причина найдена в текущем `auto_setup_env.sh`: для Isaac Sim `5.1` он клонирует актуальный `IsaacLab` `main` и не делает checkout совместимого commit. В самом script нужный commit оставлен только закомментированным. Официальная инструкция Unitree для Isaac Sim 5.1 указывает commit:

```text
80094be3245aa5c8376a7464d29cb4412ea518f5
```

Статус: **installation interrupted by upstream version mismatch**.

## Исправление

Не использовать текущий `IsaacLab main` с Python 3.11 / Isaac Sim 5.1. Переключить `~/IsaacLab` на зафиксированный Unitree commit и восстановить чистое окружение с целевыми версиями Python/PyTorch перед повторной установкой.

После исправления проверить:

```bash
conda activate unitree_sim_env
python --version
python -c "import torch; print(torch.__version__, torch.version.cuda, torch.cuda.is_available(), torch.cuda.get_device_name(0))"
isaacsim
```

Затем проверить `scripts/tutorials/00_sim/create_empty.py`, официальный G1 + Inspire task и только после этого переходить к сцене сортировщика.
