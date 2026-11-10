# TP 2 — Équilibres de Nash en stratégies pures

Programme Python qui représente un jeu fini à deux joueurs sous forme normale, calcule **toutes** les meilleures réponses, en déduit **tous** les équilibres de Nash en stratégies pures, puis teste leur **optimalité de Pareto**.

Le travail suit le cours de théorie des jeux (chapitres 2, 3 et 4) : mêmes définitions, mêmes notations (`R1`, `R2`, `BR1`, `BR2`), mêmes noms de stratégies que dans les slides, et **tous les exemples du cours servent de jeux d'essai** (exigence R7 du sujet : « les exemples étudiés en cours et en TD »).

- Aucune dépendance externe (bibliothèque standard uniquement), Python ≥ 3.8.
- Gère n'importe quelle taille `m × n` (pas forcément carrée).
- Saisie au clavier **ou** depuis un fichier texte, avec ou sans noms de stratégies.
- **Interface graphique** (Tkinter, thème sombre) qui déroule l'analyse pas à pas : meilleures réponses, équilibres, Pareto.

---

## 1. Contenu du dossier

```
tp2_nash/
├── nash_equilibrium.py     # le programme : calcul + affichage + console + interface graphique
├── test_nash.py            # 57 tests automatiques fondés sur les slides (R7)
├── README.md               # ce fichier
├── exemples/               # jeux au format fichier
│   ├── cours.txt               # exemple du sujet (= chap. 3, exercice 2)
│   ├── dilemme.txt             # dilemme du prisonnier (chap. 2), avec noms
│   ├── bataille_couple.txt     # bataille du couple (chap. 3), avec noms
│   └── decimaux.txt            # 3x2 avec gains décimaux
└── captures/               # captures d'écran de l'interface graphique
```

## 2. Lancement rapide

```bash
python nash_equilibrium.py                          # interface graphique (menu console si indisponible)
python nash_equilibrium.py --gui                    # forcer l'interface graphique
python nash_equilibrium.py --console                # menu en mode console
python nash_equilibrium.py --clavier                # saisie au clavier (console)
python nash_equilibrium.py --fichier exemples/cours.txt
python nash_equilibrium.py --exemple ex3_3          # un exemple du cours
python nash_equilibrium.py --liste-exemples         # les 18 exemples du cours
python nash_equilibrium.py --tous-les-exemples      # les lancer tous
python nash_equilibrium.py -e dilemme --sans-complements   # uniquement R2 à R6
python nash_equilibrium.py --selftest               # vérifie les 18 exemples, en console
python test_nash.py                                 # tests de validation
```

(Sous Windows, remplacer `python` par `py` si nécessaire.)

### Format du fichier d'entrée

```text
# les lignes commençant par # sont ignorées
2 2                         <- m n  (stratégies de J1, puis de J2)
J1: H B                     <- facultatif : noms des stratégies de J1
J2: G D                     <- facultatif : noms des stratégies de J2
(0, 0)   (2, 2)             <- ligne 1 : n couples (u1, u2)
(10, 11) (-1, 0)            <- ligne 2 ...
```

Règles : sans lignes `J1:` / `J2:`, les stratégies s'appellent `A1..Am` et `B1..Bn` (convention du sujet). Dans un nom, `_` devient une espace (`N'avoue_pas` → « N'avoue pas »). Les parenthèses des couples sont facultatives : seule compte la suite des nombres, lue ligne par ligne, et il en faut exactement `2·m·n`. Le séparateur décimal est le **point** (`2.5`).

### Saisie au clavier

Le programme demande `m`, `n`, les noms (Entrée = noms par défaut), puis une ligne par stratégie du joueur 1, avec `n` couples : `26,10  10,2  30,8  14,0`. Une ligne mal formée est redemandée. À la fin, il propose de sauvegarder le jeu dans un fichier réutilisable.

### Interface graphique

`python nash_equilibrium.py` ouvre une fenêtre au même style que le TP de dominance (thème sombre, boutons plats, liste déroulante de jeux). Le jeu s'affiche en matrice et l'analyse se déroule **comme à la main**, étape par étape :

1. **J1 examine chaque colonne** : la colonne clignote, puis ses meilleures réponses `R1(Bj)` apparaissent en pastille **indigo** sur `u1` ;
2. **J2 examine chaque ligne** : même chose en pastille **cyan** sur `u2` pour `R2(Ai)` ;
3. **BR1 ∩ BR2** : les cases où les deux pastilles coïncident passent en **or** (équilibres de Nash), les autres s'assombrissent ; s'il n'y en a aucun, un message l'indique ;
4. **Pareto** : pour chaque équilibre, un anneau **rouge** (dominé) ou **vert** (Pareto-optimal) l'entoure, ses dominants sont encadrés en **vert**, et une étiquette `✔ Pareto` / `✖ dominé` reste affichée ;
5. un **bilan** final.

![Étape « équilibres de Nash »](captures/gui_1_equilibre.png)

![Étape « Pareto » : l'équilibre est dominé](captures/gui_2_pareto.png)

![Jeu Dell/Compaq : trois équilibres, tous Pareto-optimaux](captures/gui_3_dell_compaq.png)

| Commande | Effet |
|---|---|
| **liste déroulante** | les 18 exemples du cours rangés par chapitre ; « Saisir une matrice… », « Jeu aléatoire… », « Charger un fichier… », « Enregistrer ce jeu… » |
| **▶ Lecture / ⏸ Pause** (`espace`) | déroule toutes les étapes ; relance depuis le début si l'analyse est terminée |
| **⏭** (`→`) · **⏮** (`←`) | étape suivante (animée) · étape précédente |
| **↺** · **⏩** | retour au jeu seul · saut direct au résultat final |
| **vitesse** | vitesse de l'animation (1 à 5) |
| **📄 Rapport** | ouvre le rapport complet (identique à la console : matrices, BR, NE, Pareto, compléments), avec « Copier » et « Enregistrer… » |

Le journal en bas de la fenêtre garde la trace de chaque étape ; la barre d'état affiche l'étape en cours (en or sur le bilan final, quand des équilibres existent).

**Saisir une matrice** : une ligne par stratégie de J1, des couples `u1,u2` séparés par des espaces, et des lignes facultatives `J1: …` / `J2: …` pour les noms (voir l'exemple pré-rempli). **Jeu aléatoire** : `m n` de 1 à 12.

**Si l'interface ne s'ouvre pas** : Tkinter est fourni avec Python sous Windows et macOS ; sous Linux, `sudo apt install python3-tk`. Sans Tkinter ou sans écran, le programme affiche un message et bascule automatiquement sur le menu console (`--gui` force l'interface et échoue avec un message si elle est impossible).

---

## 3. La théorie, pas à pas

### 3.1 Jeu sous forme normale (chap. 2)

**Analogie.** Deux restaurateurs choisissent simultanément leur menu du jour. Le bénéfice de chacun dépend de *son* choix **et** de celui de l'autre. On range tout dans un tableau : le joueur 1 choisit une **ligne**, le joueur 2 une **colonne**, et chaque case contient les deux gains.

**Définition.** Joueur 1 : `S1 = {A1..Am}` ; joueur 2 : `S2 = {B1..Bn}`. Deux matrices `A` et `B` de taille `m × n` : `A[i][j] = u1(Ai, Bj)` et `B[i][j] = u2(Ai, Bj)`. Une **issue** (un *profil*) est un couple `(Ai, Bj)`.

**Code.** `class Jeu` (attributs `A`, `B`, noms des stratégies ; propriétés `m`, `n`). Elle valide que les deux matrices sont rectangulaires, de même taille, sans `nan`/`inf`, et que les noms sont distincts.

### 3.2 Fonction de meilleure réponse (définition 3.2 du cours)

**Analogie.** « Si je sais que mon concurrent propose des pizzas, quel est mon meilleur menu ? » C'est un raisonnement *conditionnel* : on fige l'autre joueur et on optimise seul.

**Définition.**
`R1(Bj) = argmax_{Ai} u1(Ai, Bj)` — J1 regarde **une colonne** et cherche le max de **sa** matrice `A`.
`R2(Ai) = argmax_{Bj} u2(Ai, Bj)` — J2 regarde **une ligne** et cherche le max de **sa** matrice `B`.

Le cours le précise : `argmax` est un **ensemble** (une *correspondance*, pas toujours une fonction). En cas d'égalité, toutes les stratégies ex æquo sont des meilleures réponses.

**Pseudo-code.**

```text
BR1 ← ∅
pour chaque colonne j :
    g ← max sur i de A[i][j]
    pour chaque ligne i : si A[i][j] = g alors ajouter (i, j) à BR1

BR2 ← ∅
pour chaque ligne i :
    g ← max sur j de B[i][j]
    pour chaque colonne j : si B[i][j] = g alors ajouter (i, j) à BR2
```

**Code.** `meilleures_reponses_j1`, `meilleures_reponses_j2` (renvoient `{colonne: [lignes]}` et `{ligne: [colonnes]}`), puis `profils_br1`, `profils_br2` qui les transforment en ensembles de profils.

### 3.3 Équilibre de Nash en stratégies pures (définition 3.1 du cours)

**Analogie.** Deux piétons se croisent sur un trottoir (exemple du chapitre 1) et se sont chacun écartés du bon côté : si l'un change de côté *tout seul*, il se heurte à l'autre. Personne n'a intérêt à bouger seul → c'est un équilibre. Le cours parle d'accord « auto-imposé » (*self-enforcing*) : aucune pénalité n'est nécessaire pour le faire respecter.

**Définition.** `(Ai*, Bj*)` est un équilibre de Nash si
`u1(Ai*, Bj*) ≥ u1(Ak, Bj*)` pour tout `Ak`, **et** `u2(Ai*, Bj*) ≥ u2(Ai*, Bl)` pour tout `Bl`.

Équivalent : **NE = BR1 ∩ BR2**, c'est-à-dire la case est une meilleure réponse pour J1 *et* pour J2. C'est ce que calcule le programme. Le test direct par les inégalités (`est_equilibre_nash`) est aussi codé : il sert de **vérification croisée** dans les tests.

**Pseudo-code.**

```text
NE ← BR1 ∩ BR2
si NE = ∅ : afficher « aucun équilibre de Nash en stratégies pures »
```

**Complexité.** `O(m·n)` : chaque case est lue une fois pour BR1 et une fois pour BR2.

**Lien avec la dominance (proposition 3.1).** Si un jeu est solvable par élimination de stratégies *strictement* dominées, le profil obtenu est l'**unique** équilibre de Nash. Avec la dominance *faible*, on obtient bien des équilibres, mais l'élimination peut en écarter d'autres (exemple 3.4, ci-dessous).

### 3.4 Optimum de Pareto (cours, section « Optimum de Pareto »)

**Analogie.** Un partage où l'on pourrait donner plus à quelqu'un **sans rien retirer à personne** est un gaspillage. Un état où c'est impossible est Pareto-optimal.

**Définition.**
1. `s` domine `s'` si `u_i(s) ≥ u_i(s')` pour tous les joueurs **et** `u_j(s) > u_j(s')` pour au moins un joueur `j`.
2. `s*` est un optimum de Pareto s'il n'existe **aucun profil** qui le domine.

**Pseudo-code.**

```text
pour chaque s dans NE :
    Dom(s) ← { t ≠ s : u1(t) ≥ u1(s) ET u2(t) ≥ u2(s)
                        ET (u1(t) > u1(s) OU u2(t) > u2(s)) }
    si Dom(s) = ∅ : s est Pareto-optimal
    sinon           : s est dominé par les profils de Dom(s)
```

**Code.** `domine(jeu, s, t)`, `dominants(jeu, profil)`, `profils_pareto_optimaux(jeu)`. Le programme affiche pour chaque NE **tous** ses dominants, en marquant `[NE]` ceux qui sont eux-mêmes des équilibres.

### 3.5 Compléments du cours (affichés après les résultats du TP)

Ils ne sont pas demandés par le sujet mais viennent du cours ; `--sans-complements` les masque.

**Interchangeabilité (chap. 3, propriétés).** Deux équilibres `(s1*, s2*)` et `(t1*, t2*)` sont *interchangeables* si `(s1*, t2*)` et `(t1*, s2*)` sont aussi des équilibres. Code : `interchangeables()`.

**Niveau de sécurité / profil prudent (chap. 3 « Pareto versus niveau de sécurité », chap. 4).**
La garantie d'une stratégie est son pire gain : `min` sur les colonnes pour J1 (ligne par ligne de `A`), `min` sur les lignes pour J2 (colonne par colonne de `B`). Le niveau de sécurité est `v_i = max` de ces garanties ; les stratégies qui l'atteignent sont **prudentes** (maxmin). Code : `calculer_securite()`. Ce complément permet de reproduire le message du cours : *stabilité (Nash) et sécurité (maxmin) sont deux idées différentes*.

---

## 4. Trace complète sur deux exemples du cours

### 4.1 Exemple 3.3 du cours (3×3, un seul équilibre)

```text
        B1      B2      B3
A1    (6,7)   (9,6)   (0,6)
A2    (5,2)   (8,2)   (4,5)
A3    (7,7)   (7,8)   (0,9)
```

**Étape 1 — BR1 : max de `u1` dans chaque colonne**

| Colonne | `u1` (A1, A2, A3) | max | R1 |
|---|---|---|---|
| B1 | 6, 5, 7 | 7 | {A3} |
| B2 | 9, 8, 7 | 9 | {A1} |
| B3 | 0, 4, 0 | 4 | {A2} |

BR1 = {(A3,B1), (A1,B2), (A2,B3)} — exactement ce que dit le slide.

**Étape 2 — BR2 : max de `u2` dans chaque ligne**

| Ligne | `u2` (B1, B2, B3) | max | R2 |
|---|---|---|---|
| A1 | 7, 6, 6 | 7 | {B1} |
| A2 | 2, 2, 5 | 5 | {B3} |
| A3 | 7, 8, 9 | 9 | {B3} |

BR2 = {(A1,B1), (A2,B3), (A3,B3)} — idem.

**Étape 3 — Intersection.** BR1 ∩ BR2 = **{(A2,B3)}**, de gains **(4, 5)**.

**Étape 4 — Pareto.** `(A1,B1) = (6,7)` fait mieux pour les deux joueurs ; `(A3,B1) = (7,7)` et `(A3,B2) = (7,8)` aussi. Donc l'unique équilibre est **dominé** : il est stable mais pas efficace. Les profils Pareto-optimaux du jeu sont (A1,B2), (A3,B2) et (A3,B3).

### 4.2 Exercice 2 du chapitre 3 = exemple du sujet (4×4)

| Colonne | `u1` (A1..A4) | max | R1 |
|---|---|---|---|
| B1 | 26, 2, 24, 4 | 26 | {A1} |
| B2 | 10, 2, 8, 0 | 10 | {A1} |
| B3 | 30, 22, 28, 20 | 30 | {A1} |
| B4 | 14, 22, 8, 16 | 22 | {A2} |

| Ligne | `u2` (B1..B4) | max | R2 |
|---|---|---|---|
| A1 | 10, 2, 8, 0 | 10 | {B1} |
| A2 | 2, 2, 8, 8 | 8 | {B3, B4} ← ex æquo |
| A3 | 8, 0, 8, 2 | 8 | {B1, B3} ← ex æquo |
| A4 | 0, 10, 8, 10 | 10 | {B2, B4} ← ex æquo |

BR1 ∩ BR2 = **{(A1,B1), (A2,B4)}**, de gains (26, 10) et (22, 8). Pareto : `(A1,B1)` est optimal ; `(A2,B4)` est dominé par `(A1,B1)` (strictement sur les deux gains, c'est celui cité par le cours) et **faiblement** par `(A1,B3) = (30,8)`, `(A3,B1) = (24,8)` et `(A3,B3) = (28,8)` (gain de J2 égal, gain de J1 strictement plus grand). Le cours commente : le premier équilibre correspond à « dire la vérité / y croire », le second est fragile.

---

## 5. Du sujet au code

| Exigence | Où dans le code |
|---|---|
| **R1** Saisie (clavier / fichier) | `saisir_jeu_clavier()`, `lire_fichier()`, `jeu_depuis_nombres()` |
| **R2** Matrices + affichage des couples | `class Jeu`, `formater_matrice_gains()`, `formater_jeu()` |
| **R3** Toutes les meilleures réponses | `meilleures_reponses_j1()`, `meilleures_reponses_j2()` |
| **R4** Intersection → équilibres | `profils_br1()`, `profils_br2()`, `analyser()` |
| **R5** Affichage + message si aucun NE | `formater_meilleures_reponses()`, `formater_equilibres()` |
| **R6** Pareto | `domine()`, `dominants()`, `formater_pareto()` |
| **R7** Tests | `EXEMPLES` (18 jeux du cours), `test_nash.py` (57 tests), `--selftest` |
| *Complément* Interchangeabilité | `interchangeables()`, `formater_interchangeabilite()` |
| *Complément* Sécurité / maxmin | `calculer_securite()`, `formater_securite()` |
| *Interface* Étapes de l'analyse | `construire_etapes()` → liste d'`Etape` (testable sans écran) |
| *Interface* Fenêtre, animation, dessin | `class App` (Tkinter) : `animate()`, `redraw()` |
| *Interface* Saisie d'une matrice | `jeu_depuis_texte()` |

---

## 6. Exemple d'exécution (extrait réel)

`python nash_equilibrium.py --exemple ex3_3 --sans-complements` (fin de la sortie) :

```text
Meilleures réponses du joueur 1 (selon la colonne jouée par le joueur 2) :
  R1(B1) = {A3}    [u1 max = 7]
  R1(B2) = {A1}    [u1 max = 9]
  R1(B3) = {A2}    [u1 max = 4]
Meilleures réponses du joueur 2 (selon la ligne jouée par le joueur 1) :
  R2(A1) = {B1}    [u2 max = 7]
  R2(A2) = {B3}    [u2 max = 5]
  R2(A3) = {B3}    [u2 max = 9]
BR1 = {(A1, B2), (A2, B3), (A3, B1)}
BR2 = {(A1, B1), (A2, B3), (A3, B3)}

Matrice annotée (* = gain d'une meilleure réponse ; deux * = équilibre de Nash) :
+---------+---------+---------+----------+
| J1 \ J2 |    B1   |    B2   |    B3    |
+---------+---------+---------+----------+
| A1      | (6, 7*) | (9*, 6) |  (0, 6)  |
+---------+---------+---------+----------+
| A2      |  (5, 2) |  (8, 2) | (4*, 5*) |
+---------+---------+---------+----------+
| A3      | (7*, 7) |  (7, 8) | (0, 9*)  |
+---------+---------+---------+----------+

Équilibres de Nash en stratégies pures (BR1 inter BR2) : 1
  (A2, B3)  ->  gains (4, 5)

Optimalité de Pareto des équilibres de Nash :
  (A2, B3) (4, 5) : DOMINÉ au sens de Pareto par (A1, B1)=(6, 7), (A1, B2)=(9, 6), (A3, B1)=(7, 7), (A3, B2)=(7, 8)
  -> NE Pareto-optimaux : {}
  -> NE dominés         : {(A2, B3)}
Profils Pareto-optimaux du jeu (tous profils confondus) : {(A1, B2), (A3, B2), (A3, B3)}
```

Lecture de la matrice annotée : une étoile après `u1` signale que la ligne est une meilleure réponse de J1 dans cette colonne ; une étoile après `u2`, que la colonne est une meilleure réponse de J2 dans cette ligne. **Deux étoiles = équilibre de Nash.**

Quand il n'y a aucun équilibre (`--exemple tir_au_but`) :

```text
Aucun équilibre de Nash en stratégies pures : BR1 inter BR2 est vide.
(Un équilibre en stratégies mixtes existe toujours, mais il sort du cadre de ce TP.)
```

Exemple de complément (`--exemple poule_mouillee`, chapitre 4) :

```text
Niveau de sécurité (maxmin en stratégies pures, cours chap. 3 et 4) :
  ...
  Profil(s) prudent(s) (maxmin) :
    (Dévier, Dévier) gains (0, 0) -> équilibre de Nash : non
```

C'est la phrase du cours : « (Dévier, Dévier) est un équilibre maxmin qui n'est pas un équilibre de Nash ».

---

## 7. Jeux d'essai : les exemples du cours (R7)

| Clé | Source dans le cours | Ce qu'il illustre | Équilibres purs |
|---|---|---|---|
| `sujet` | chap. 3, exercice 2 (= TP §3) | plusieurs NE, ex æquo pour J2, un NE dominé | (A1,B1), (A2,B4) |
| `ex3_1` | chap. 3, exemple 3.1 | 2 NE, un optimal, un dominé | (B,G), (H,D) |
| `ex3_2` | chap. 3, exemple 3.2 | un seul NE, Pareto-optimal | (B,R) |
| `ex3_3` | chap. 3, exemple 3.3 | un seul NE, **dominé** | (A2,B3) |
| `ex3_4` | chap. 3, exemple 3.4 | ex æquo ; la dominance faible écarte (B,G) | (B,G), (H,D) |
| `carrefour` | chap. 3, jeux célèbres | 2 NE Pareto-optimaux, non interchangeables | (P,S), (S,P) |
| `pierre_feuille_ciseaux` | chap. 3, jeux célèbres | **aucun** NE pur (3×3) | — |
| `bataille_couple` | chap. 3, jeux célèbres | 2 NE Pareto-optimaux | (Théâtre,Théâtre), (Foot,Foot) |
| `tir_au_but` | chap. 3, extension mixte | **aucun** NE pur (2×2) | — |
| `dell_compaq` | chap. 3, exercice 1 | ex æquo des deux joueurs, 3 NE | (W,A), (W,B), (L,D) |
| `chiffre` | chap. 3, optimum de Pareto, ex. 1 | 10×10, 10 NE, un seul optimal | (a,a) pour a = 1..10 |
| `securite` | chap. 3, Pareto vs sécurité, ex. 2 | NE optimal mais garantie 0 | (U,U), (V,V) |
| `dilemme` | chap. 2 | NE **dominé** | (Avoue,Avoue) |
| `essd_chap2` | chap. 2, élimination itérative | le résultat de l'ESSD est l'unique NE | (H,G) |
| `dominance_faible_chap2` | chap. 2, ordre d'élimination | 4 NE, dont 2 dominés | (T,C), (M,L), (M,R), (B,L) |
| `poule_mouillee` | chap. 4, Nash vs maxmin | le profil maxmin n'est pas un NE | (C,D), (D,C) |
| `maxmin_chap4` | chap. 4, paiement maxmin | 3×2 ; maxmin (T,L) ≠ NE (B,R) | (B,R) |
| `maxmin_multiple` | chap. 4, plusieurs maxmin | 2 profils prudents, aucun NE pur | — |

Cette table couvre toutes les catégories exigées par le sujet : un seul NE, plusieurs NE, aucun NE, plusieurs meilleures réponses pour un même joueur, NE Pareto-optimaux et NE dominés (plus un jeu non carré et un jeu 10×10).

**Validation.** `test_nash.py` vérifie :
1. les ensembles BR1, BR2 et NE **recopiés des slides** (exercice 2, exemple 3.3, Dell/Compaq) ;
2. les équilibres et les NE dominés attendus de chacun des 18 exemples ;
3. les affirmations du cours : le seul profil non Pareto-optimal du dilemme est son équilibre, 10 NE et un seul optimum dans le jeu du chiffre, la proposition 3.1, le profil maxmin de la poule mouillée, `v1 = 2` et `v2 = 1` au chapitre 4 ;
4. sur 500 jeux aléatoires pleins d'égalités, que `BR1 ∩ BR2` coïncide avec le test direct de la définition 3.1 ;
5. sur 200 jeux aléatoires, que `profils_pareto_optimaux` coïncide avec une recherche exhaustive indépendante ;
6. sur 300 jeux aléatoires, que le gain d'un équilibre est toujours ≥ au niveau de sécurité du joueur ;
7. la lecture/écriture de fichiers (avec noms) et les cas d'erreur (matrice non rectangulaire, mauvais nombre de gains ou de noms, fichier mal formé, `nan`, jeu 1×1) ;
8. les **étapes de l'interface** pour chacun des 18 exemples (nombre d'étapes, marques cumulatives, verdicts de Pareto, absence d'étape Pareto s'il n'y a pas d'équilibre) et la saisie de matrice en texte ;
9. l'**interface elle-même** (5 tests : chargement et dessin des 18 exemples jusqu'au bout, pas à pas, retour, lecture automatique, annulation d'une animation, rapport). Ils exigent un écran et sont **ignorés automatiquement** sinon ; sous Linux sans écran : `xvfb-run -a python test_nash.py`.

---

## 8. Pièges classiques (à connaître pour l'examen)

| Importance | Piège | À retenir |
|---|---|---|
| ★★★ | Max par colonne / par ligne **inversé** | J1 compare **dans une colonne** (il change de ligne) ; J2 compare **dans une ligne** (il change de colonne). |
| ★★★ | **Oublier les ex æquo** | Une meilleure réponse est un *ensemble*. Cocher une seule case sur `R2(A2) = {B3, B4}` fait rater un équilibre. |
| ★★★ | « Nash ⇒ Pareto-optimal » | **Faux.** Dilemme du prisonnier, exemple 3.3 : l'équilibre est dominé. |
| ★★★ | Dominance **faible** et équilibres | L'élimination de stratégies faiblement dominées peut **écarter** des équilibres (exemple 3.4 : on trouve (H,D), pas (B,G)) et dépend de l'ordre (chap. 2). Seule la dominance *stricte* garantit l'unicité (prop. 3.1). |
| ★★ | Domination et inégalité stricte | Il faut `≥` partout **et** `>` quelque part. Deux profils aux gains identiques ne se dominent pas. |
| ★★ | Comparer seulement entre équilibres | Le sujet demande d'être dominé par **d'autres profils quelconques** : `(A2,B4)` est dominé par `(A1,B3)`, qui n'est pas un NE. |
| ★★ | Nash = maxmin ? | **Non** en général (stabilité ≠ sécurité) : poule mouillée. Ils coïncident quand chaque joueur a une stratégie dominante (corollaires du chap. 4), comme dans le dilemme. |
| ★★ | Pareto vs sécurité | `(U,U)` = (9,9) est Pareto-optimal mais ne garantit que 0 ; `(V,V)` = (7,7) est dominé mais garantit 7 (chap. 3). |
| ★★ | « Pas de NE pur ⇒ pas de NE » | Faux : un NE en stratégies **mixtes** existe toujours (théorème de Nash 1951, chap. 3). Ici on ne cherche que les purs. |
| ★ | Interchangeabilité | Deux NE ne sont pas toujours interchangeables (carrefour, bataille du couple). |
| ★ | Égalité de flottants | `0.1 + 0.2 == 0.3` vaut `False` en Python. Le code compare avec `math.isclose`. |
| ★ | Indices | Le code compte à partir de 0 (`(0,0)`), l'affichage à partir de 1 (`(A1,B1)`). |

---

## 9. Questions d'entraînement

**Q1.** Dans le dilemme du prisonnier, montrer que le seul profil qui n'est pas Pareto-optimal est l'équilibre de Nash (remarque du cours).
*Réponse.* `(Avoue,Avoue) = (-5,-5)` est dominé par `(N'avoue pas, N'avoue pas) = (-1,-1)`. Les trois autres profils sont optimaux : `(Avoue, N'avoue pas) = (0,-10)` donne à J1 son gain maximal ; `(N'avoue pas, Avoue) = (-10,0)` donne à J2 le sien ; `(N'avoue pas, N'avoue pas) = (-1,-1)` n'est dominé par aucun profil (les deux autres cases rapportent moins à l'un des joueurs). Le programme le confirme : `python nash_equilibrium.py -e dilemme`.

**Q2.** Jeu Dell/Compaq : combien d'équilibres, et lesquels sont interchangeables ?
*Réponse.* Trois : `(W,A)`, `(W,B)`, `(L,D)`. `(W,A)` et `(W,B)` sont interchangeables (les profils croisés sont eux-mêmes des NE). Aucun des deux ne l'est avec `(L,D)` : `(W,D)` n'est pas un NE. Compaq a 4 stratégies car elles sont des **plans d'action** conditionnels au choix de Dell.

**Q3.** Exemple 3.4 : pourquoi l'élimination de stratégies faiblement dominées ne trouve-t-elle que (H,D) ?
*Réponse.* Pour J1, `H = (10,5)` domine faiblement `B = (10,2)` (égalité en G, strictement mieux en D). On élimine B, et avec lui l'équilibre (B,G) ; il reste la ligne H où J2 préfère D (2 > 0). Or `(B,G) = (10,11)` est bien un NE (et il domine (H,D) au sens de Pareto).

**Q4.** Jeu du chiffre (1 à 10) : pourquoi `(a,b)` avec `a ≠ b` n'est-il jamais un NE ?
*Réponse.* Les deux joueurs gagnent 0. J1 peut dévier vers `b` et obtenir `10·b > 0` : déviation profitable. Les `(a,a)` sont des NE (dévier fait passer de `10a` à 0), mais seul `(10,10)`, de gains (100,100), est Pareto-optimal.

**Q5.** Poule mouillée : quel est le profil prudent, et pourquoi n'est-ce pas un équilibre ?
*Réponse.* `Continuer` garantit au pire −100, `Dévier` au pire −10 : les deux joueurs sont prudents en déviant, d'où `(Dévier, Dévier) = (0,0)`. Mais si J2 dévie, J1 gagne 10 en continuant : déviation profitable, donc ce n'est pas un NE. Les NE sont `(Continuer, Dévier)` et `(Dévier, Continuer)`.

**Q6.** Un jeu `m × n` **sans aucune égalité** de gains peut avoir au plus combien d'équilibres purs ?
*Réponse.* Au plus `min(m, n)`. Sans égalité, BR1 a exactement `n` cases (une par colonne) et BR2 exactement `m` cases (une par ligne) ; l'intersection ne peut dépasser le plus petit des deux. Avec des égalités, ce peut être jusqu'à `m·n` (tous les gains égaux).

---

## 10. Choix de conception et limites

- **Meilleures réponses = ensembles**, pas des valeurs uniques : c'est la clé de l'exactitude (R3).
- **Deux méthodes indépendantes** pour les équilibres (intersection des BR et test direct des inégalités) : si elles divergeaient, les tests le détecteraient.
- **Pareto sur tous les profils du jeu**, conformément à la définition du cours ; le programme affiche aussi les profils Pareto-optimaux de tout le jeu.
- **Stratégies pures uniquement** (comme demandé). Le cours traite aussi, dans les chapitres suivants, l'élimination itérative de stratégies dominées (chap. 2), les équilibres en stratégies mixtes (fin du chap. 3) et les points selle des jeux à somme nulle (chap. 4) : ces notions ne sont **pas** implémentées ici et pourraient en être des extensions naturelles.
- Le niveau de sécurité est calculé en **stratégies pures** : le cours montre (chap. 4) que ce niveau peut être strictement amélioré par des stratégies mixtes.
- Les noms de stratégies par défaut sont `A1..Am` et `B1..Bn`, comme dans le sujet.
- **Un seul fichier** pour le moteur et l'interface, comme le TP de dominance : Tkinter est importé dans un `try`, donc console, tests et `--selftest` fonctionnent sans lui. L'interface ne recalcule rien : elle affiche les étapes produites par `construire_etapes()`, ce qui garantit que l'écran et la console donnent les mêmes résultats.
