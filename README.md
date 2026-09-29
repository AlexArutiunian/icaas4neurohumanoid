# icaas4neurohumanoid

Рабочий репозиторий для симуляции и экспериментов с Unitree G1 в Isaac Sim / Isaac Lab.

## Быстрый тест верхней части

Для запущенного `Isaac-PickPlace-RedBlock-G129-Inspire-Joint`:

```bash
conda activate unitree_sim_env
cd ~/icaas4neurohumanoid
python tools/upper_body_keyboard.py
```

Клавиши: `1/2/3` — левая/правая/обе руки вверх, `4` — рабочая поза, `0` — home, `o/c` — открыть/закрыть Inspire, `q` — выход.

Скрипт использует DDS domain `1`, как `unitree_sim_isaaclab`, и предназначен для симуляции.

## Документация

- [История проекта](docs/history/README.md) — краткий журнал проверок, установок, исправлений и принятых технических решений.
