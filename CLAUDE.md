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
- `scrProgress` : carte de chaleur, classement des tables, évolution des notes, historique.
- `scrCount` : compte à rebours 3-2-1.
- `scrGame` : le calcul, le sablier en SVG animé par `requestAnimationFrame`, le pavé numérique.
- `scrResult` : note, points, étoiles, détail de chaque calcul.

Autres éléments :
- La barre `#kidbar` contient l'avatar, le prénom, le bouton 🎨 et les onglets. Elle est visible sur les écrans Setup, Progress et Result.
- Le header contient le menu `⋮` (export / import). Il est masqué pendant le jeu via `body.playing`.
- `show()` applique aussi le thème de l'enfant courant et la classe `body.playing`.

## Modèle de données (localStorage)

Clé `tablo.v1`. L'ancienne clé `basimaths.v2` est relue automatiquement si la nouvelle est absente (`OLD_KEYS`).

```js
db = { kids: [Kid], currentId: "id" }
Kid = {
  id, name (≤ 20 car.), avatar (emoji de AVATARS), created,
  settings: { type: "add"|"mul"|"dm", addTables: [0..10], mulTables: [2..10],
              dmKinds: {double, half}, dmParts: [1..3], count (10 | 20 | 40, constante COUNT_CHOICES), time (s),
              mode: "random"|"smart", voice: bool, theme: "lagon"|"bonbon"|"arcade" },
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
  - juste en 3 s ou moins : 1 ;
  - juste entre 3 et 10 s : linéaire de 1 à 0,5 ;
  - juste en 10 s ou plus : 0,5.
- **Maîtrise d'un calcul** (`mastery`) : moyenne pondérée des essais, avec un poids × 0,75 à chaque essai plus ancien, divisée par `Σpoids + 0,3` (a priori prudent). Elle vaut `null` si le calcul n'a jamais été vu.
- **Niveaux** : < 0,40 non acquis, < 0,65 fragile, < 0,85 en cours, sinon acquis.
- **Couleur** (`heat`) : teinte HSL de 0 (rouge) à 125 (vert). Elle est indépendante du thème.
- **Score d'une table** (`groupStats`) : moyenne des maîtrises de ses calculs, un calcul jamais vu comptant 0. Le classement va du plus acquis au moins acquis.
- **Mode intelligent** (`smartSequence`) : tirage pondéré avec remise, par `smartWeight` :
  - calcul jamais vu : poids 1 ;
  - sinon : `(1 − m)^1,5 + 0,06`, plus 0,6 si le dernier essai était faux.
  - Un même calcul est tiré au plus `ceil(2n / taille du pool)` fois, et jamais deux fois de suite.
- Le bouton « S'entraîner sur les 3 moins acquises » sélectionne les 3 groupes les plus faibles et passe en mode intelligent.

## Voix (Web Speech API)

- `webkitSpeechRecognition` en `fr-FR`, continu, avec résultats intermédiaires, 5 alternatives, et redémarrage automatique sur `onend`.
- Tolérant au bavardage et au bruit (`onVoiceResult`) :
  - si la bonne réponse apparaît dans n'importe quel nombre de n'importe quelle alternative, **même intermédiaire**, elle est validée tout de suite ;
  - une phrase sans nombre est ignorée en silence (plus de « je n'ai pas compris ») ;
  - un nombre faux ne compte que dans un résultat **final** ;
  - `voice.used` mémorise l'index du résultat déjà utilisé : sa version finale tardive ne compte pas pour le calcul suivant.
- `parseFrNumbers()` renvoie tous les nombres prononcés ; `parseFrNumber()` renvoie le **dernier** nombre prononcé, écrit en chiffres ou en toutes lettres (quatre-vingt-dix-neuf, soixante et onze, mille, plus quelques homophones comme « sans » pour cent). Il est exposé sous `window.__tablo` pour les tests.
- Une réponse vocale retire 0,6 s au temps mesuré, pour compenser la latence de la reconnaissance.
- Navigateurs : Chrome, Edge et Safari, mais pas Firefox. Chrome envoie l'audio aux serveurs de Google, donc il faut Internet.

## Thèmes

- Trois thèmes, définis par des variables CSS sur `:root[data-theme=…]` : **lagon** (par défaut, également appliqué à `:root` seul), **bonbon** et **arcade** (sombre).
- Chaque thème définit les variables : `--bg --card --ink --muted --line --chip --none --keybg --accent --accent-ink --add --dm --mul --ok --ok-ink --ko --sand --star --glass --shadow`.
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
- **À chaque modification des fichiers servis, incrémenter `CACHE` dans `sw.js`** (actuellement `tablo-v11`).
- Le jeton `gh` de l'utilisateur ne peut ni créer de dépôt ni configurer Pages. **Ne jamais proposer `gh auth login`** : ça casserait ses accès à d'autres projets. Ce n'est de toute façon plus nécessaire, Pages est déjà activé.
- Vérifier la mise en ligne : `curl -s https://thomaspoinsot.github.io/tablo/tablo.html | grep -q "<texte ajouté>"`, à relancer toutes les 10 s jusqu'à ce que le texte apparaisse.
- Les commits se terminent par `Co-Authored-By: Claude …`.

## Tests

`dev/check.sh` lance trois vérifications :
1. la syntaxe JS de chaque bloc `<script>` (`node --check`) ;
2. les tests de `parseFrNumber` ;
3. des captures d'écran avec Chrome en mode automatique, à 375×667, 820×1180 et 1366×768, sur les écrans kids, setup, progression et jeu, avec des données de test générées par `dev/make_test_pages.py`.

Il faut ensuite regarder les PNG produits. Points à connaître :
- Les captures prises juste après une navigation peuvent paraître pâles : c'est l'animation `fade` des écrans, pas un bug.
- `--virtual-time-budget` n'avance pas toujours `requestAnimationFrame`. Pour tester un parcours de jeu, il vaut mieux simuler des frappes clavier avec `KeyboardEvent("keydown")` que d'attendre le sablier.
- Pour tester le service worker ou le manifeste, il faut servir en http (`python3 -m http.server`), pas en `file://`.

## Pièges et choix déjà faits

- Le stockage passe par localStorage et pas par des cookies : les cookies sont limités à 4 Ko et Chrome ne les garde pas en `file://`. Chaque appareil, et même l'appli installée sur iOS par rapport à Safari, a son propre stockage. Le transfert se fait par export / import.
- Un seul type de calcul par séance (pas de mélange), à la demande de l'utilisateur, par souci de clarté.
- **La table du 1 est exclue**, à la demande de l'utilisateur : ni table ×1, ni calcul « × 1 » dans les autres tables. Tout passe par la constante `MUL_RANGE = range(2, 10)`, et `normalizeKid()` retire le 1 des anciens réglages. Les anciens essais `mul:1:*` et `mul:*:1` restent dans les sauvegardes, mais ne sont plus affichés.
- Responsive : téléphone, tablette et PC sont tous testés. Sur téléphone, l'écran de jeu doit tenir sans défiler (media queries `max-height`, unités `dvh`). Les petits écrans affichent des libellés courts (`.tl-long` et `.tl-short`).
- `color-mix()`, `dvh` et `aspect-ratio` sont simplement ignorés par les vieux navigateurs : seul l'effet visuel est perdu, rien ne plante. Éviter en revanche le JS récent (`?.`, `??`, `.at()`, `structuredClone`…) : l'appli tourne sur une tablette Android 8.1 avec un Chrome figé.
- Le header a `z-index: 40` pour que le menu ⋮ passe au-dessus des écrans animés : l'animation `fade` utilise `transform`, ce qui crée un contexte d'empilement.
