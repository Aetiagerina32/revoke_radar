# RevokeRadar

Утилита для аудита и подготовки транзакций на отзыв (revoke) устаревших или избыточных ERC‑20 разрешений (`approve`).

## Возможности

- Сканирует все токены вашего кошелька через Ethplorer API.
- Проверяет текущий `allowance(owner → spender)` для списка спендеров.
- Для каждого ненулевого разрешения готовит транзакцию `approve(spender, 0)` (revoke).
- Поддержка Dry‑Run и реальной отправки через Web3.

## Установка

```bash
git clone https://github.com/ваш‑профиль/RevokeRadar.git
cd RevokeRadar
pip install -r requirements.txt
