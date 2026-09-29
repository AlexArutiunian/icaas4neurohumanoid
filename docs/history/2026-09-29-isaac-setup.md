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
| Conda | установлена через Miniconda |

Системный Python не изменяем: Isaac/Unitree устанавливаются в отдельное окружение.

## Серверный baseline

По предоставленной инструкции серверный стек подготовлен на Isaac Sim `5.1.0` и Isaac Lab; удалённый GUI запускается через WebRTC поверх ZeroTier. Серверное администраторское окружение не изменяем без необходимости.

## Принятые решения

1. Использовать официальный `unitreerobotics/unitree_sim_isaaclab`, а не собирать G1 вручную поверх чистого Isaac Sim.
2. Использовать Isaac Sim `5.1`, чтобы локальная среда соответствовала серверному baseline.
3. Держать всё в отдельном `unitree_sim_env`.
4. Для Isaac Sim 5.1 использовать совместимый Isaac Lab commit `80094be3245aa5c8376a7464d29cb4412ea518f5`, указанный Unitree.
5. RTX 3080 Ti использовать для GUI/сцены/отладки; тяжёлые прогоны и обучение — на RTX 5090.

## Ход установки

### Assets и CycloneDDS

Официальные Unitree assets скачаны и распакованы (`assets.zip`, около 1.2 GB). CycloneDDS собран и установлен в `~/cyclonedds/install`.

### Conda

Miniconda установлена и инициализирована. Приняты Terms of Service стандартных Anaconda channels.

### Исправление Isaac Lab

Первая попытка через текущий `auto_setup_env.sh` подтянула `IsaacLab main`, который уже требует Python `>=3.12`, и обновила зависимости до `torch 2.12.0 + cu130`. Для Isaac Sim 5.1 это оказалось несовместимо с окружением Unitree на Python 3.11.

`~/IsaacLab` переключён на совместимый commit:

```text
80094be3245aa5c8376a7464d29cb4412ea518f5
```

`unitree_sim_env` пересоздан, pinned Isaac Lab установлен успешно, EULA NVIDIA принята.

### Unitree dependencies

Установлены `unitree_sdk2_python`, зависимости `unitree_sim_isaaclab` и editable-пакет `teleimager 1.5.0`. В процессе `opencv-python` приведён к версии `4.11.0.86`.

Проверка CUDA:

```text
Torch: 2.7.0+cu128
CUDA: 12.8
CUDA available: True
GPU: NVIDIA GeForce RTX 3080 Ti Laptop GPU
```

### Runtime

Isaac Sim GUI успешно запущен локально на RTX 3080 Ti. Asset Browser работает; cloud assets read-only, но доступны для использования в сцене. Проверено добавление humanoid asset в Stage.

Базовый Isaac Lab runtime успешно запущен через:

```bash
cd ~/IsaacLab
./isaaclab.sh -p scripts/tutorials/00_sim/create_empty.py
```

Открылось окно Isaac Sim 5.1.0 с пустой сценой и `PhysicsScene`; получены `Simulation App Startup Complete` и `[INFO]: Setup complete...`.

### Первый запуск G1 + Inspire

Запущен официальный task:

```bash
python sim_main.py \
  --device cpu \
  --enable_cameras \
  --task Isaac-PickPlace-RedBlock-G129-Inspire-Joint \
  --enable_inspire_dds \
  --robot_type g129
```

На этапе загрузки появились MDL/Shader warnings для части материалов warehouse asset, но они не оказались блокирующими. Сцена загрузилась и simulation loop работает: в терминале печатается `While loop execution frequency statistics` с устойчивой частотой около 4 Hz.

Робот найден через Stage и визуально подтверждён в viewport: загружен Unitree G1 с Inspire hands рядом с рабочим столом в warehouse-сцене. Стол и объект task также присутствуют.

Статус: **локальная установка Isaac Sim + Isaac Lab + официальный Unitree G1/Inspire runtime полностью подтверждена**.

### Управление верхней частью

Добавлен `tools/upper_body_keyboard.py` для простого ручного теста текущего fixed-base task без Wholebody locomotion. Скрипт работает через те же DDS topics, которые использует официальный Unitree simulator: `rt/lowcmd` для 14 суставов рук и `rt/inspire/cmd` для Inspire hands. Используется DDS domain `1`, как в `unitree_sim_isaaclab`.

Команды: `1/2/3` — левая/правая/обе руки вверх, `4` — рабочая поза, `0` — home, `o/c` — открыть/закрыть Inspire, `q` — выход. Переходы сделаны плавными ограничением скорости.

Статус утилиты: **добавлена, runtime-проверка на локальной сцене ещё не выполнена**.

## Следующий шаг

Проверить `tools/upper_body_keyboard.py` в запущенном `Isaac-PickPlace-RedBlock-G129-Inspire-Joint`. После подтверждения управления перейти к собственной задаче сортировки: выделить sorter task, затем поэтапно добавить conveyor, accept/reject bins, камеры и генератор тестовых объектов. Сначала сохранить детерминированное управление/IK и только после стабильного baseline добавлять обучение и массовые прогоны на RTX 5090.
