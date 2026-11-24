# Tablo — notes de reprise

Appli web de révision du calcul mental pour enfants (niveau CE1 et plus), en français. Elle couvre les tables d'addition, les doubles et moitiés, et les tables de multiplication. Les calculs arrivent un par un avec un sablier ; chaque séance donne une note sur 20 et des points selon la vitesse de réponse.

- En ligne : <https://thomaspoinsot.github.io/tablo/> (GitHub Pages, dépôt public `ThomasPoinsot/tablo`)
- Le dossier local s'appelle encore `basimaths/` : c'était l'ancien nom de l'appli. C'est normal.
- L'utilisateur communique en français : UI, commentaires, commits et réponses en français.

## Fichiers

| Fichier | Rôle |
|---|---|
| `tablo.html` | **Toute l'appli** : HTML + CSS + JS inline, sans aucune dépendance. Fonctionne seul en double-clic (`file://`). |
| `index.html` | Redirige vers `tablo.html`. Il ne doit **pas** déclarer de manifeste (voir Android ≤ 9). |
| `manifest.webmanifest` | Installation comme appli (PWA). Chargé dynamiquement par `tablo.html`. |
| `sw.js` | Service worker : mode hors-ligne, stratégie réseau d'abord puis cache. |
| `icons/` | `icon-192.png`, `icon-512.png`, `apple-touch-icon.png` (180 px). |
| `dev/` | Outils de test : `check.sh` et `make_test_pages.py`. Hors appli. |

**Contrainte forte : l'appli doit tenir dans un seul fichier.** L'utilisateur y tient. Les autres fichiers sont des bonus pour l'hébergement, et `tablo.html` doit continuer à marcher sans eux. L'icône est aussi intégrée en data-URI dans `tablo.html` : il y a deux occurrences, `apple-touch-icon` et `icon`.

## Architecture de `tablo.html`

Tout le JS est dans une IIFE `(() => { "use strict"; ... })()`. Il n'y a ni framework, ni build, ni dépendance externe. Les sections du code sont repérées par des bannières `// ====`, dans cet ordre :
Outils → Données de référence → Sauvegarde → Écran enfants → Navigation → Catalogue des calculs → Maîtrise → Écran réglages → Choix des calculs → Reconnaissance vocale → Partie → Fin de partie → Écran progression → Installation → Démarrage.

Écrans : des `<section class="screen">`, un seul actif à la fois, géré par `show(id)`.

- `scrKids` : choix de l'enfant, ajout et édition dans `<dialog id="dlgKid">`.
- `scrSetup` : réglages de la séance.
- `scrProgress` : barre « Progression générale », carte de chaleur, classement des tables, évolution des notes, historique.
- `scrCount` : compte à rebours 3-2-1.
- `scrGame` : le calcul, le sablier en SVG animé par `requestAnimationFrame`, le pavé numérique.
- `scrResult` : note, points, étoiles, carte « Ta progression », détail de chaque calcul.

Autres éléments :
- La barre `#kidbar` contient l'avatar, le prénom, le bouton 🎨 et les onglets. Elle est visible sur les écrans Setup, Progress et Result.
- Le header contient le menu `⋮` (export / import, test du micro). Il est masqué pendant le jeu via `body.playing`.
- `show()` applique aussi le thème de l'enfant courant et la classe `body.playing`.

## Modèle de données (localStorage)

Clé `tablo.v1`. L'ancienne clé `basimaths.v2` est relue automatiquement si la nouvelle est absente (`OLD_KEYS`).

```js
db = { kids: [Kid], currentId: "id" }
Kid = {
  id, name (≤ 20 car.), avatar (emoji de AVATARS), created,
  settings: { type: "add"|"mul"|"dm", addTables: [0..10], mulTables: [2..10],
              dmKinds: {double, half}, dmParts: [1..3], count (toujours 20, SESSION_COUNT), time (5|8|10|15|20 s, TIME_CHOICES),
              mode: toujours "smart", voice: toujours false, theme: "lagon"|"bonbon"|"arcade" },
  history: [{ d (timestamp), type, mode: "random"|"smart", n, time, good, note, pts }],  // plus récent en premier, max 200
  records: { "type|mode|n|time": points },
  facts:   { factKey: [[ok 0|1, secondes, (1 si révision)], ...] }  // 10 derniers essais par calcul, plus ancien en premier
}
```

- **« Revoir mes erreurs » (mode `"errors"`) ne compte pas comme une séance** : ni note, ni historique, ni record (l'enfant vient de voir la correction). Ses essais vont quand même dans `facts`, marqués `[ok, temps, 1]` : une bonne réponse y vaut 0,5 dans `attemptScore`, elle n'entre pas dans le temps moyen, et elle n'annule pas le bonus « raté la dernière fois » du mode intelligent. L'écran de fin masque note, points et étoiles et affiche « Erreurs corrigées x/n ». `normalizeKid()` retire les anciennes séances `"errors"` de l'historique.
- `normalizeKid()` complète les champs manquants. **Il faut le mettre à jour à chaque nouveau réglage**, pour rester compatible avec les anciennes sauvegardes et les imports.
- Clés des faits :
  - additions : `add:T:B`, avec T = la table (0..10) et B entre 0 et 10 ;
  - multiplications : `mul:T:B`, avec T et B entre 2 et 10 (constante `MUL_RANGE`) ;
  - doubles et moitiés : `double:N` et `half:N`.
- Pour l'addition et la multiplication, l'affichage inverse les termes une fois sur deux (`finalize`). La stat reste rangée sous la table choisie.
- Export : fichier JSON `{ app: "Tablo", version: 1, exported, kids, currentId }`. Import : `parseDb()` valide le fichier, puis il remplace tout après confirmation.

## Contenu pédagogique

Doubles et moitiés : la constante `DM_SHEET` suit **exactement** les fiches « Je mémorise » MHM 2025 CE1 fournies par l'utilisateur, en 3 parties.

- La fiche des moitiés (partie 1) **n'a pas « moitié de 18 »**. Le contenu suit la fiche à la lettre, et l'utilisateur a été prévenu.
- Doubles :
  - partie 1 : 1 à 15 ;
  - partie 2 : 20, 25, 30, 35, 40, 45, 50 ;
  - partie 3 : 100, 150, 200, 250, 300, 350, 500.
- Moitiés :
  - partie 1 : 2 à 16 (nombres pairs), puis 20 à 30 ;
  - partie 2 : 40 à 100, de 10 en 10 ;
  - partie 3 : 200, 300, 400, 500, 600, 1000.

## Algorithmes

- **Pas de touche OK** : au clavier, la réponse est validée automatiquement dès qu'elle a autant de chiffres que la bonne réponse, qu'elle soit juste ou fausse (`pressKey`). Le pavé : 7 8 9 / 4 5 6 / 1 2 3 / (vide) 0 ⌫. La touche Entrée ne sert plus pendant le jeu.
- **Temps de réponse** : au clavier, une bonne réponse est chronométrée à l'appui sur son **premier chiffre** (`game.firstT`, remis à zéro si le premier chiffre est effacé ou changé), pour ne pas pénaliser la vitesse de frappe. Une réponse fausse garde le temps jusqu'à la validation. À la voix : temps de reconnaissance − 0,6 s.
- **Points d'une bonne réponse** : `round(10 + 90 × temps restant / temps alloué)`, plus un combo de `min(série − 1, 10) × 5`. Une erreur ou un temps écoulé donne 0 point et remet la série à zéro.
- **Note sur 20** : bonnes réponses / total × 20, arrondi au demi-point. Étoiles : 3 si 100 %, 2 si ≥ 75 %, 1 si ≥ 50 %.
- **Score d'un essai** (`attemptScore`) :
  - faux : 0 ;
  - juste en révision (« Revoir mes erreurs ») : 0,5 ;
  - juste en 4 s ou moins : 1 ;
  - juste entre 4 et 12 s : linéaire de 1 à 0,5 ;
  - juste en 12 s ou plus : 0,5.
- **Maîtrise d'un calcul** (`mastery`) : moyenne pondérée des essais, avec un poids × 0,75 à chaque essai plus ancien, divisée par `Σpoids + 0,3` (a priori prudent). Elle vaut `null` si le calcul n'a jamais été vu.
- **Niveaux** (constantes `FRAGILE`, `EN_COURS`, `ACQUIRED`) : < 0,40 non acquis, < 0,65 fragile, < 0,80 en cours, sinon acquis. Allégé le 2026-11-23 (avant : 0,85 et 3 s / 10 s dans `attemptScore`).
- **Couleur** (`heat` / `LEVELS`) : une couleur franche par niveau (rouge, orange, jaune, vert), indépendante du thème. L'ancien dégradé continu rendait « en cours » et « acquis » trop proches. Légende en 4 pastilles.
- **Barres de niveaux** (`lvBar`, `lvCounts`, `lvLegend`) : barre empilée acquis → en cours → fragile → non acquis → jamais vu. Utilisée pour la progression générale d'un type, chaque ligne du classement (trié par nombre d'acquis, puis score ; à droite « acquis/total ») et la carte « Ta progression » de fin de séance (`renderResultProgress`) : sélection = tables des réglages + tables des calculs joués, barre animée de l'état avant la séance vers l'état après (`lvAnimate`), nouveaux acquis, acquis perdus (« À consolider »), une barre par table si plusieurs.
- **Score d'une table** (`groupStats`) : moyenne des maîtrises de ses calculs, un calcul jamais vu comptant 0. Le classement va du plus acquis au moins acquis.
- **Mode intelligent** (`smartSequence`) : tirage pondéré avec remise, par `smartWeight` :
  - calcul jamais vu : poids 1 ;
  - sinon : `(1 − m)^1,5 + 0,06`, plus 0,6 si le dernier essai était faux.
  - Un même calcul est tiré au plus `ceil(2n / taille du pool)` fois, et jamais deux fois de suite.
- Le bouton « S'entraîner sur les 3 moins acquises » sélectionne les 3 groupes les plus faibles et passe en mode intelligent.

## Voix (Web Speech API)

- `webkitSpeechRecognition` en `fr-FR`, continu, résultats intermédiaires, 5 alternatives, relancé sur `onend`. **Essayé puis abandonné** : sessions courtes (`continuous = false`) sur Android et relance de l'écoute à chaque réponse. Sur la tablette Android 8.1, ça ne marchait plus qu'une fois sur 5 (micro sourd pendant les relances).
- **Constat sur appareil** : la reconnaissance de Google ignore souvent un nombre dit tout seul (« seize » ne déclenche rien) mais comprend bien une phrase. L'enfant est donc invité à répondre « ça fait … » (`VOICE_PROMPT`, consignes du compte à rebours et des réglages).
- **Seule la bonne réponse est validée à la voix** (`onVoiceResult`) : dès qu'elle apparaît dans n'importe quelle alternative, même intermédiaire. Un nombre faux ou mal reconnu est seulement affiché (« « 54 » ? Redis ! »), le sablier continue ; s'il se vide, c'est une erreur.
- Tolérance (`voiceCandidates` / `voiceHeardExpected`, exposé dans `window.__tablo`) : sons proches `VOICE_ALIASES` (oui→huit, si→six, cette→sept, vin→vingt, sans→cent…) et combinaisons de nombres voisins (« 50 6 » → 56, « 5 6 » → 56, « 300 50 » → 350). « de » est neutralisé pour ne pas compter 2 dans « moitié de… ». Éviter d'ajouter des mots courants comme alias.
- `voice.used` mémorise l'index du résultat déjà utilisé : sa version finale tardive ne compte pas pour le calcul suivant.
- `parseFrNumbers` lit les textes mixtes (« cinquante 6 » → 50, 6, puis recollés en 56 par `voiceCandidates`).
- **Retiré le 2026-11-24** : le choix « Comment répondre ? » et le test du micro (menu ⋮, `dlgMic`, journal des événements). `normalizeKid()` force `voice: false`. Le moteur de reconnaissance (`voiceStart`, `onVoiceResult`…) reste dans le code, inactif, pour pouvoir remettre la voix plus tard (le test du micro est dans l'historique git, commit 96310c4).
- `parseFrNumbers()` renvoie tous les nombres prononcés ; `parseFrNumber()` renvoie le **dernier** nombre prononcé, écrit en chiffres ou en toutes lettres (quatre-vingt-dix-neuf, soixante et onze, mille, plus quelques homophones comme « sans » pour cent). Il est exposé sous `window.__tablo` pour les tests.
- Une réponse vocale retire 0,6 s au temps mesuré, pour compenser la latence de la reconnaissance.
- Navigateurs : Chrome, Edge et Safari, mais pas Firefox. Chrome envoie l'audio aux serveurs de Google, donc il faut Internet.

- **Statut (2026-11-22)** : sur la tablette Android 8.1, ça marche pour des phrases mais pas pour un nombre dit seul. L'utilisateur pense qu'il n'y a pas de vraie solution avec la Web Speech API, et je suis d'accord : impossible de « biaiser » Chrome vers des nombres. Options proposées, **décision prise le 2026-11-24 : voix retirée de l'interface « pour l'instant »** (option 2) :
  1. garder la voix avec la consigne « ça fait … » (c'est ce qui est en ligne) et voir à l'usage ;
  2. retirer le mode vocal, ou le cacher dans le menu ⋮ comme option expérimentale ;
  3. reconnaissance hors ligne (Vosk, modèle d'environ 40 Mo) : déconseillée, car elle casse le fichier unique et elle est trop lourde pour la tablette.

## Thèmes

- Trois thèmes, définis par des variables CSS sur `:root[data-theme=…]` : **lagon** (par défaut, également appliqué à `:root` seul), **bonbon** et **arcade** (sombre).
- Chaque thème définit les variables : `--bg --card --ink --muted --line --chip --none --keybg --accent --accent-ink --add --dm --mul --ok --ok-ink --ko --sand --star --glass --sel --sel-ink --off --off-ink --shadow`.
- **Sélection uniforme** (2026-11-24, demande de l'utilisateur) : toute case choisie (`.chip.on`, `.type.on`) prend la même couleur `--sel` / `--sel-ink`, quel que soit le type de calcul. Une case non choisie est entièrement gris pâle (`--off` / `--off-ink`, symbole des grandes cases en niveaux de gris). Ne plus colorer les sélections avec `--add`, `--dm` ou `--mul`.
- Le choix est enregistré par enfant (`settings.theme`). On le change avec le bouton 🎨 de la kidbar (il fait défiler les thèmes) ou dans la fiche de l'enfant. `applyTheme()` met aussi à jour `<meta name="theme-color">`.
- Pour ajouter un thème : un bloc CSS, une entrée dans `THEMES` (couleurs des vignettes) et une entrée dans `THEME_ORDER`.

## Installation sur l'écran d'accueil / PWA

- iPhone : les balises `apple-mobile-web-app-*` et l'`apple-touch-icon` intégrée suffisent, même sans manifeste.
- Le manifeste est ajouté dynamiquement (script dans `<head>`), et **seulement en http(s)**.
- **Android ≤ 9 : pas de manifeste.** Sur une Galaxy Tab A 2016 sous Android 8.1, l'appli installée par Chrome (WebAPK) plantait au lancement (« l'application s'est arrêtée »). Sans manifeste, Chrome crée un simple raccourci, et ça marche : c'est validé sur l'appareil.
- Chrome réduit son user-agent et annonce toujours « Android 10 ». La vraie version est donc lue via `navigator.userAgentData.getHighEntropyValues(["platformVersion"])`, avec repli sur le user-agent. Le script positionne alors `window.__oldAndroid` et `window.__androidVersion`.
- Le bouton « 📱 Ajouter à l'écran d'accueil » appelle `beforeinstallprompt` quand il est disponible. Sinon, il affiche des instructions selon l'appareil : iOS, Android ancien, Android, PC, ou fichier local.
- Le manifeste n'a pas d'icône `maskable` : elle a été retirée pendant le débogage Android 8.1. Elle n'était pas la cause, mais il est inutile de la remettre.

## Déploiement

- Pour mettre à jour : **commit, puis `git push`** (remote SSH `git@github.com:ThomasPoinsot/tablo.git`, branche `main`). GitHub Pages se redéploie tout seul en 30 à 60 s.
- **À chaque modification des fichiers servis, incrémenter `CACHE` dans `sw.js`** (actuellement `tablo-v18`).
- Le jeton `gh` de l'utilisateur ne peut ni créer de dépôt ni configurer Pages. **Ne jamais proposer `gh auth login`** : ça casserait ses accès à d'autres projets. Ce n'est de toute façon plus nécessaire, Pages est déjà activé.
- Vérifier la mise en ligne : `curl -s https://thomaspoinsot.github.io/tablo/tablo.html | grep -q "<texte ajouté>"`, à relancer toutes les 10 s jusqu'à ce que le texte apparaisse.
- Les commits se terminent par `Co-Authored-By: Claude …`.

## Tests

`dev/check.sh` lance trois vérifications :
1. la syntaxe JS de chaque bloc `<script>` (`node --check`) ;
2. les tests de `parseFrNumber` ;
3. des captures d'écran avec Chrome en mode automatique, à 375×667, 820×1180 et 1366×768, sur les écrans kids, setup, progression et jeu, avec des données de test générées par `dev/make_test_pages.py`.

`make_test_pages.py` produit aussi `v_result.html` (séance complète jouée au clavier, 3e réponse fausse), non capturé par `check.sh` : le lancer à la main avec `--virtual-time-budget=40000` et une fenêtre haute (ex. 375×1500).

Il faut ensuite regarder les PNG produits. Points à connaître :
- Les captures prises juste après une navigation peuvent paraître pâles : c'est l'animation `fade` des écrans, pas un bug.
- `--virtual-time-budget` n'avance pas toujours `requestAnimationFrame`. Pour tester un parcours de jeu, il vaut mieux simuler des frappes clavier avec `KeyboardEvent("keydown")` que d'attendre le sablier.
- Pour tester le service worker ou le manifeste, il faut servir en http (`python3 -m http.server`), pas en `file://`.

## Évolutions récentes (toutes en ligne)

2026-11-24 — écran de réglages simplifié, à la demande de l'utilisateur :
- Plus de choix « Comment choisir les calculs » : toujours le mode intelligent. Le texte d'explication et les calculs prioritaires (`modeInfo`) sont affichés sous le choix des tables.
- Plus de choix « Nombre de calculs » : toujours des séries de 20 (`SESSION_COUNT`).
- Plus de choix « Comment répondre » ni de test du micro : réponse au clavier seulement (voir Voix).
- Temps par calcul : 5, 8, 10, 15, 20 s (3 s et 30 s retirés ; `normalizeKid()` ramène les anciens réglages au plus proche).
- Inactivité (`checkIdle`) : après 30 min sans interaction (vérifié toutes les 30 s et au retour de veille via `visibilitychange`/`focus`), la page est **rechargée** pour récupérer la dernière version. Au redémarrage (`resumeAfterIdle`, via `sessionStorage` `tablo.resume`) : plusieurs enfants → écran de choix de l'enfant ; un seul → on revient sur l'écran d'avant (Progression, sinon Réglages).

2026-11-23 :
- Couleurs de maîtrise : une couleur franche par niveau (rouge, orange, jaune, vert) au lieu du dégradé, où « en cours » et « acquis » se confondaient. Légende en pastilles.
- « Acquis » un peu plus facile : seuil 0,85 → 0,80, réponse pleinement rapide jusqu'à 4 s (au lieu de 3 s), minimum 0,5 à 12 s (au lieu de 10 s). Un calcul devient acquis après 2 bonnes réponses en moins de 4 s, ou en 5 s ; une seule ne suffit pas.
- Barres de progression par niveau, demandées par l'utilisateur « dans le suivi de progression après partie » et « à la fin » : barre « Progression générale » dans l'onglet Progression, barre par table dans le classement, carte « Ta progression » sur l'écran de fin (avant → après animé, nouveaux acquis, acquis à consolider). Voir Algorithmes → Barres de niveaux.

2026-11-22 :
- « Revoir mes erreurs » ne compte plus comme une séance (pas de 20/20 sur 3 calculs refaits). Ses essais comptent quand même à moitié pour chaque calcul (voir Modèle de données).
- Temps de réponse au clavier compté au premier chiffre d'une bonne réponse : la vitesse de frappe ne pénalise plus l'acquisition.
- Plus de touche OK : validation automatique au bon nombre de chiffres. Le 0 est au centre de la dernière ligne du pavé.
- Voix : seule la bonne réponse valide, tolérance aux sons proches, test du micro, consigne « ça fait … ». Voir la section Voix et son statut.

Pistes proposées mais jamais demandées (ne pas faire sans accord) : retirer +0 des tables d'addition, mettre « Ajouter à l'écran d'accueil » dans le menu ⋮, ajouter « moitié de 18 ».

## Pièges et choix déjà faits

- Le stockage passe par localStorage et pas par des cookies : les cookies sont limités à 4 Ko et Chrome ne les garde pas en `file://`. Chaque appareil, et même l'appli installée sur iOS par rapport à Safari, a son propre stockage. Le transfert se fait par export / import.
- Un seul type de calcul par séance (pas de mélange), à la demande de l'utilisateur, par souci de clarté.
- **La table du 1 est exclue**, à la demande de l'utilisateur : ni table ×1, ni calcul « × 1 » dans les autres tables. Tout passe par la constante `MUL_RANGE = range(2, 10)`, et `normalizeKid()` retire le 1 des anciens réglages. Les anciens essais `mul:1:*` et `mul:*:1` restent dans les sauvegardes, mais ne sont plus affichés.
- Responsive : téléphone, tablette et PC sont tous testés. Sur téléphone, l'écran de jeu doit tenir sans défiler (media queries `max-height`, unités `dvh`). Les petits écrans affichent des libellés courts (`.tl-long` et `.tl-short`).
- `color-mix()`, `dvh` et `aspect-ratio` sont simplement ignorés par les vieux navigateurs : seul l'effet visuel est perdu, rien ne plante. Éviter en revanche le JS récent (`?.`, `??`, `.at()`, `structuredClone`…) : l'appli tourne sur une tablette Android 8.1 avec un Chrome figé.
- Le header a `z-index: 40` pour que le menu ⋮ passe au-dessus des écrans animés : l'animation `fade` utilise `transform`, ce qui crée un contexte d'empilement.
