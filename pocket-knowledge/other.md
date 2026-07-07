# Expertise other — appris par Pocket
- (2026-07-06) Label GitHub 'cat:content' n'existait pas dans le repo — créé (couleur 0e8a16) avant de l'appliquer aux tâches de rédaction.
- (2026-07-07) Gaspard veut une notif push quand une tâche longue (ex: expansion du vault) se termine — l'infra existe déjà (pocket.yml step 'Notify (push)' + scripts/pocket_push.py, VAPID) et se déclenche auto en fin de tâche pocket via:phone. Vérifier que l'appareil 'ordinateur' est bien abonné (pocket-data/sub-*.json) via la PWA.
- (2026-07-07) Notif fin de tâche CLI locale (hors Pocket) : hors de portée du cloud, ça se règle avec un hook Stop local (~/.claude/settings.json), à poser via /update-config en session Claude Code locale — pas via Pocket.
