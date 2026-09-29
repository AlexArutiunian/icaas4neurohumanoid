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

### 1. Assets

Официальные Unitree assets скачаны и распакованы успешно (`assets.zip`, около 1.2 GB).

### 2. CycloneDDS

CycloneDDS собран и установлен в `~/cyclonedds/install`.

### 3. Conda

Miniconda установлена и инициализирована. Отдельно приняты Terms of Service стандартных Anaconda channels.

### 4. Первая попытка Isaac Lab

Первый запуск официального setup script для Isaac Sim 5.1 дошёл до установки Isaac Lab, но использовал актуальный `IsaacLab main`. Он уже требовал Python `>=3.12`, тогда как окружение Unitree создано на Python `3.11.16`. Перед остановкой зависимости также были обновлены до `torch 2.12.0 + cu130`.

Причина: в `auto_setup_env.sh` совместимый Isaac Lab commit для 5.1 оставлен закомментированным, поэтому checkout автоматически не выполняется.

### 5. Исправление версии Isaac Lab

`~/IsaacLab` переключён на commit, указанный Unitree для Isaac Sim 5.1:

```text
80094be3245aa5c8376a7464d29cb4412ea518f5
```

Окружение `unitree_sim_env` пересоздано на Python `3.11`. Установка pinned Isaac Lab завершилась без фатальной ошибки; EULA NVIDIA принята. В финальном шаге установлены `torch 2.7.0+cu128`, `torchvision 0.22.0+cu128`, `triton 3.3.0`.

Предупреждение о недостающем `isaacsim/.vscode/settings.json` относится только к VSCode `python.analysis.extraPaths` и не блокирует работу Isaac Lab.

Статус: **Isaac Lab installed; Unitree dependencies and runtime verification pending**.

## Следующий шаг

Доставить оставшиеся зависимости Unitree и патч `libstdc++`:

```bash
export CYCLONEDDS_HOME="$HOME/cyclonedds/install"

cd ~/unitree_sdk2_python
pip install -e .

cd ~/unitree_sim_isaaclab
pip install -r requirements.txt

cd teleimager
pip install -e .
cd ..

conda install -y -c conda-forge libstdcxx-ng
```

После этого проверить фактические версии и GPU:

```bash
python -c "import torch; print(torch.__version__, torch.version.cuda, torch.cuda.is_available(), torch.cuda.get_device_name(0))"
```

Затем проверить запуск `isaacsim`, `scripts/tutorials/00_sim/create_empty.py`, официальный G1 + Inspire task и только после этого переходить к сцене сортировщика.
