#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TP 2 - Théorie des jeux : équilibres de Nash en stratégies pures
================================================================

Jeu fini à deux joueurs sous forme normale (cours, chapitres 2 et 3) :
    - le joueur 1 a m stratégies  (lignes de la matrice)
    - le joueur 2 a n stratégies  (colonnes de la matrice)
    - deux matrices de gains : A (joueur 1) et B (joueur 2)
    - noms de stratégies : A1..Am / B1..Bn par défaut (sujet du TP), ou noms libres
      comme dans les slides (H, B, G, D, Pierre, Théâtre, Avoue, ...)

Le programme :
    R1  saisit le jeu (clavier ou fichier)
    R2  affiche les matrices de gains et la matrice des couples (u1, u2)
    R3  calcule TOUTES les meilleures réponses (ex æquo compris)       [cours, déf. 3.2]
    R4  calcule les équilibres de Nash purs = BR1 inter BR2            [cours, déf. 3.1]
    R5  affiche meilleures réponses, équilibres et gains (ou un message explicite)
    R6  analyse l'optimalité de Pareto de chaque équilibre             [cours, optimum de Pareto]
    R7  fournit les jeux d'essai du cours (voir aussi test_nash.py)

Compléments du cours (affichés après les résultats du TP, désactivables) :
    - interchangeabilité des équilibres de Nash                        [cours, chap. 3, propriétés]
    - niveau de sécurité / profil prudent (maxmin en stratégies pures) [cours, chap. 3 et 4]

Interface graphique (Tkinter, thème sombre) : le jeu s'affiche en matrice, puis l'analyse se
déroule pas à pas : meilleures réponses de J1 (colonnes), de J2 (lignes), équilibres de Nash,
Pareto. Boutons ▶ lecture, ⏭ pas à pas, ⏮ retour, ↺ début ; flèches du clavier et espace.

Usage rapide :
    python nash_equilibrium.py                       # interface graphique (menu console sinon)
    python nash_equilibrium.py --console             # menu en mode console
    python nash_equilibrium.py --fichier exemples/cours.txt
    python nash_equilibrium.py --exemple ex3_3
    python nash_equilibrium.py --tous-les-exemples
    python nash_equilibrium.py --selftest            # vérifie les 18 exemples du cours
"""

from __future__ import annotations

import argparse
import math
import random
import re
import sys
from dataclasses import dataclass
from typing import Dict, FrozenSet, List, Optional, Sequence, Set, Tuple

try:  # l'interface graphique est facultative : le reste du programme marche sans Tkinter
    import tkinter as tk
    import tkinter.font as tkfont
    from tkinter import filedialog, messagebox, simpledialog
    HAS_TK = True
except Exception:  # Tkinter absent (Linux : sudo apt install python3-tk)
    HAS_TK = False

# Un profil de stratégies est un couple d'indices (i, j) commençant à 0 :
# (0, 0) correspond au profil (A1, B1) du sujet.
Profil = Tuple[int, int]
Nombre = float  # int ou float, selon ce que l'utilisateur saisit


# =============================================================================
# 1. Représentation du jeu (R1, R2)
# =============================================================================

def _egal(a: Nombre, b: Nombre) -> bool:
    """Égalité de deux gains avec tolérance (évite le piège 0.1 + 0.2 != 0.3)."""
    return math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-9)


def _sup_ou_egal(a: Nombre, b: Nombre) -> bool:
    """a >= b, avec tolérance sur l'égalité."""
    return a > b or _egal(a, b)


def _strict_sup(a: Nombre, b: Nombre) -> bool:
    """a > b strictement, avec tolérance sur l'égalité."""
    return a > b and not _egal(a, b)


@dataclass
class Jeu:
    """Jeu fini à deux joueurs sous forme normale.

    A[i][j] = u1(Ai, Bj)   gain du joueur 1
    B[i][j] = u2(Ai, Bj)   gain du joueur 2
    noms_j1 / noms_j2 : noms des stratégies (A1..Am et B1..Bn par défaut)
    """

    A: List[List[Nombre]]
    B: List[List[Nombre]]
    nom: str = "Jeu"
    noms_j1: Optional[List[str]] = None
    noms_j2: Optional[List[str]] = None

    def __post_init__(self) -> None:
        if not self.A or not self.A[0]:
            raise ValueError("Le jeu doit avoir au moins une stratégie par joueur.")
        n = len(self.A[0])
        for matrice, etiquette in ((self.A, "A"), (self.B, "B")):
            if any(len(ligne) != n for ligne in matrice):
                raise ValueError(f"La matrice {etiquette} n'est pas rectangulaire.")
            if any(not math.isfinite(x) for ligne in matrice for x in ligne):
                raise ValueError(f"La matrice {etiquette} contient une valeur non finie.")
        if len(self.B) != len(self.A) or len(self.B[0]) != n:
            raise ValueError("Les matrices A et B doivent avoir les mêmes dimensions.")
        if self.noms_j1 is None:
            self.noms_j1 = [f"A{i + 1}" for i in range(self.m)]
        if self.noms_j2 is None:
            self.noms_j2 = [f"B{j + 1}" for j in range(self.n)]
        for noms, attendu, joueur in ((self.noms_j1, self.m, 1), (self.noms_j2, self.n, 2)):
            if len(noms) != attendu:
                raise ValueError(f"Joueur {joueur} : {attendu} noms de stratégies attendus, "
                                 f"{len(noms)} reçus.")
            if len(set(noms)) != len(noms):
                raise ValueError(f"Joueur {joueur} : deux stratégies portent le même nom.")

    @property
    def m(self) -> int:
        """Nombre de stratégies du joueur 1 (lignes)."""
        return len(self.A)

    @property
    def n(self) -> int:
        """Nombre de stratégies du joueur 2 (colonnes)."""
        return len(self.A[0])

    def nom_j1(self, i: int) -> str:
        return self.noms_j1[i]

    def nom_j2(self, j: int) -> str:
        return self.noms_j2[j]

    def nom_profil(self, profil: Profil) -> str:
        return f"({self.nom_j1(profil[0])}, {self.nom_j2(profil[1])})"

    def noms_par_defaut(self) -> bool:
        return (self.noms_j1 == [f"A{i + 1}" for i in range(self.m)]
                and self.noms_j2 == [f"B{j + 1}" for j in range(self.n)])

    def gains(self, profil: Profil) -> Tuple[Nombre, Nombre]:
        i, j = profil
        return self.A[i][j], self.B[i][j]

    def profils(self) -> List[Profil]:
        return [(i, j) for i in range(self.m) for j in range(self.n)]


def fmt(x: Nombre) -> str:
    """Affichage compact d'un gain : 26 plutôt que 26.0."""
    if float(x).is_integer():
        return str(int(x))
    return format(x, ".10g")


def jeu_depuis_couples(couples: Sequence[Sequence[Tuple[Nombre, Nombre]]], nom: str = "Jeu",
                       noms_j1: Optional[List[str]] = None,
                       noms_j2: Optional[List[str]] = None) -> Jeu:
    """Construit un jeu à partir d'une matrice de couples (u1, u2), comme dans les slides."""
    A = [[c[0] for c in ligne] for ligne in couples]
    B = [[c[1] for c in ligne] for ligne in couples]
    return Jeu(A, B, nom, noms_j1, noms_j2)


# =============================================================================
# 2. Saisie : fichier et clavier (R1)
# =============================================================================

_RE_NOMBRE = re.compile(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")


def extraire_nombres(texte: str) -> List[Nombre]:
    """Extrait tous les nombres d'un texte ; '(26, 10) (10, 2)' -> [26, 10, 10, 2].

    Le séparateur décimal est le POINT (2.5) ; la virgule sépare u1 de u2.
    """
    resultat: List[Nombre] = []
    for jeton in _RE_NOMBRE.findall(texte):
        try:
            resultat.append(int(jeton))
        except ValueError:
            resultat.append(float(jeton))
    return resultat


def _decouper_noms(texte: str) -> List[str]:
    """'H B' -> ['H', 'B'] ; les '_' deviennent des espaces : N_avoue_pas -> 'N avoue pas'."""
    return [t.replace("_", " ") for t in re.split(r"[\s,;]+", texte.strip()) if t]


def jeu_depuis_nombres(m: int, n: int, nombres: Sequence[Nombre], nom: str = "Jeu",
                       noms_j1: Optional[List[str]] = None,
                       noms_j2: Optional[List[str]] = None) -> Jeu:
    """Construit le jeu à partir de 2*m*n nombres : u1,u2 de (A1,B1), puis (A1,B2), ..."""
    if len(nombres) != 2 * m * n:
        raise ValueError(
            f"{2 * m * n} nombres attendus ({m}x{n} couples de gains), "
            f"{len(nombres)} trouvés."
        )
    A = [[0] * n for _ in range(m)]
    B = [[0] * n for _ in range(m)]
    it = iter(nombres)
    for i in range(m):
        for j in range(n):
            A[i][j] = next(it)
            B[i][j] = next(it)
    return Jeu(A, B, nom, noms_j1, noms_j2)


def lire_fichier(chemin: str) -> Jeu:
    """Lit un jeu depuis un fichier texte.

    Format :
        # commentaire (ignoré)
        m n
        J1: H B            <- facultatif : noms des m stratégies du joueur 1
        J2: G D            <- facultatif : noms des n stratégies du joueur 2
        (u1, u2) (u1, u2) ...      <- ligne 1 : n couples
        ...                        <- m lignes au total
    Les parenthèses sont facultatives ; seule compte la suite des nombres.
    """
    with open(chemin, encoding="utf-8-sig") as f:
        lignes = [ligne.split("#", 1)[0].strip() for ligne in f]
    lignes = [ligne for ligne in lignes if ligne]
    if not lignes:
        raise ValueError(f"Le fichier '{chemin}' est vide.")
    entete = re.fullmatch(r"(\d+)\s*[\s,;xX]\s*(\d+)", lignes[0])
    if not entete:
        raise ValueError("La première ligne doit contenir 'm n' (ex. : 4 4).")
    m, n = int(entete.group(1)), int(entete.group(2))
    if m < 1 or n < 1:
        raise ValueError("m et n doivent être >= 1.")
    noms: Dict[int, Optional[List[str]]] = {1: None, 2: None}
    lignes_gains: List[str] = []
    for ligne in lignes[1:]:
        correspondance = re.fullmatch(r"[Jj]([12])\s*:\s*(.*)", ligne)
        if correspondance:
            noms[int(correspondance.group(1))] = _decouper_noms(correspondance.group(2))
        else:
            lignes_gains.append(ligne)
    nombres = extraire_nombres(" ".join(lignes_gains))
    return jeu_depuis_nombres(m, n, nombres, nom=chemin, noms_j1=noms[1], noms_j2=noms[2])


def ecrire_fichier(jeu: Jeu, chemin: str) -> None:
    """Sauvegarde un jeu dans le format lisible par lire_fichier()."""
    with open(chemin, "w", encoding="utf-8") as f:
        f.write(f"# {jeu.nom}\n{jeu.m} {jeu.n}\n")
        if not jeu.noms_par_defaut():
            f.write("J1: " + " ".join(s.replace(" ", "_") for s in jeu.noms_j1) + "\n")
            f.write("J2: " + " ".join(s.replace(" ", "_") for s in jeu.noms_j2) + "\n")
        for i in range(jeu.m):
            f.write(" ".join(f"({fmt(jeu.A[i][j])}, {fmt(jeu.B[i][j])})"
                             for j in range(jeu.n)) + "\n")


def jeu_depuis_texte(texte: str, nom: str = "Jeu saisi") -> Jeu:
    """Jeu à partir d'un texte libre (zone de saisie de l'interface graphique).

    Une ligne = une stratégie du joueur 1, avec ses couples 'u1,u2' séparés par des espaces.
    Lignes facultatives 'J1: ...' et 'J2: ...' pour nommer les stratégies ; '#' = commentaire.
    Contrairement à lire_fichier(), pas d'en-tête 'm n' : m et n se déduisent des lignes.
    """
    noms: Dict[int, Optional[List[str]]] = {1: None, 2: None}
    lignes_gains: List[str] = []
    for brut in texte.splitlines():
        ligne = brut.split("#", 1)[0].strip()
        if not ligne:
            continue
        correspondance = re.fullmatch(r"[Jj]([12])\s*:\s*(.*)", ligne)
        if correspondance:
            noms[int(correspondance.group(1))] = _decouper_noms(correspondance.group(2))
        else:
            lignes_gains.append(ligne)
    if not lignes_gains:
        raise ValueError("Aucune ligne de gains.")
    rangees = [extraire_nombres(ligne) for ligne in lignes_gains]
    tailles = {len(r) for r in rangees}
    if len(tailles) != 1:
        raise ValueError("Les lignes n'ont pas toutes le même nombre de couples.")
    k = tailles.pop()
    if k == 0 or k % 2:
        raise ValueError("Chaque ligne doit contenir des couples 'u1,u2' (nombre pair de gains).")
    return jeu_depuis_nombres(len(rangees), k // 2, [x for r in rangees for x in r],
                              nom, noms[1], noms[2])


def _lire_entier(invite: str, minimum: int = 1) -> int:
    while True:
        try:
            valeur = int(input(invite).strip())
            if valeur >= minimum:
                return valeur
        except ValueError:
            pass
        print(f"  -> Entrée invalide : un entier >= {minimum} est attendu.")


def _lire_noms(invite: str, attendu: int) -> Optional[List[str]]:
    """Demande des noms de stratégies ; Entrée vide = noms par défaut (None)."""
    while True:
        noms = _decouper_noms(input(invite))
        if not noms:
            return None
        if len(noms) == attendu and len(set(noms)) == attendu:
            return noms
        print(f"  -> {attendu} noms distincts attendus, séparés par des espaces.")


def saisir_jeu_clavier() -> Jeu:
    """Saisie interactive : m, n, noms facultatifs, puis une ligne de n couples par ligne."""
    print("\n--- Saisie du jeu ---")
    m = _lire_entier("Nombre de stratégies du joueur 1 (m) : ")
    n = _lire_entier("Nombre de stratégies du joueur 2 (n) : ")
    noms_j1 = _lire_noms(f"Noms des {m} stratégies du joueur 1 (Entrée = A1..A{m}) : ", m)
    noms_j2 = _lire_noms(f"Noms des {n} stratégies du joueur 2 (Entrée = B1..B{n}) : ", n)
    etiquettes = noms_j1 or [f"A{i + 1}" for i in range(m)]
    print(f"Pour chaque ligne, entrez {n} couple(s) 'u1,u2' séparés par des espaces.")
    print("Exemple : 26,10  10,2  30,8  14,0")
    nombres: List[Nombre] = []
    for i in range(m):
        while True:
            texte = input(f"  Ligne {etiquettes[i]} : ")
            ligne = extraire_nombres(texte)
            if len(ligne) == 2 * n:
                nombres.extend(ligne)
                break
            print(f"  -> {2 * n} nombres attendus ({n} couples), {len(ligne)} reçus. Réessayez.")
    return jeu_depuis_nombres(m, n, nombres, "Jeu saisi au clavier", noms_j1, noms_j2)


# =============================================================================
# 3. Meilleures réponses et équilibres de Nash (R3, R4)
# =============================================================================

def meilleures_reponses_j1(jeu: Jeu) -> Dict[int, List[int]]:
    """R1(Bj) = arg max_i u1(Ai, Bj), pour chaque colonne j.

    On renvoie la liste de TOUTES les lignes qui atteignent le maximum.
    """
    reponses: Dict[int, List[int]] = {}
    for j in range(jeu.n):
        colonne = [jeu.A[i][j] for i in range(jeu.m)]
        gain_max = max(colonne)
        reponses[j] = [i for i, g in enumerate(colonne) if _egal(g, gain_max)]
    return reponses


def meilleures_reponses_j2(jeu: Jeu) -> Dict[int, List[int]]:
    """R2(Ai) = arg max_j u2(Ai, Bj), pour chaque ligne i (toutes les colonnes ex æquo)."""
    reponses: Dict[int, List[int]] = {}
    for i in range(jeu.m):
        ligne = jeu.B[i]
        gain_max = max(ligne)
        reponses[i] = [j for j, g in enumerate(ligne) if _egal(g, gain_max)]
    return reponses


def profils_br1(br1: Dict[int, List[int]]) -> Set[Profil]:
    """BR1 = {(Ai, Bj) : Ai in R1(Bj)}"""
    return {(i, j) for j, lignes in br1.items() for i in lignes}


def profils_br2(br2: Dict[int, List[int]]) -> Set[Profil]:
    """BR2 = {(Ai, Bj) : Bj in R2(Ai)}"""
    return {(i, j) for i, colonnes in br2.items() for j in colonnes}


def est_equilibre_nash(jeu: Jeu, profil: Profil) -> bool:
    """Test DIRECT de la définition 3.1 du cours (inégalités), indépendant des BR.

    Sert de vérification croisée dans test_nash.py.
    """
    i, j = profil
    ok1 = all(_sup_ou_egal(jeu.A[i][j], jeu.A[k][j]) for k in range(jeu.m))
    ok2 = all(_sup_ou_egal(jeu.B[i][j], jeu.B[i][l]) for l in range(jeu.n))
    return ok1 and ok2


def interchangeables(jeu: Jeu, s: Profil, t: Profil) -> bool:
    """Cours, chap. 3 (propriétés) : deux équilibres s* = (s1*, s2*) et t* = (t1*, t2*)
    sont interchangeables ssi (s1*, t2*) et (t1*, s2*) sont aussi des équilibres de Nash."""
    (i, j), (k, l) = s, t
    return est_equilibre_nash(jeu, (i, l)) and est_equilibre_nash(jeu, (k, j))


# =============================================================================
# 4. Optimalité de Pareto (R6)
# =============================================================================

def domine(jeu: Jeu, s: Profil, t: Profil) -> bool:
    """True si s domine t au sens de Pareto (cours : optimum de Pareto, définition 1) :
    u_i(s) >= u_i(t) pour les deux joueurs, avec au moins une inégalité STRICTE."""
    u1s, u2s = jeu.gains(s)
    u1t, u2t = jeu.gains(t)
    return (_sup_ou_egal(u1s, u1t) and _sup_ou_egal(u2s, u2t)
            and (_strict_sup(u1s, u1t) or _strict_sup(u2s, u2t)))


def dominants(jeu: Jeu, profil: Profil) -> List[Profil]:
    """Tous les profils du jeu (équilibres ou non) qui dominent `profil`."""
    return [t for t in jeu.profils() if t != profil and domine(jeu, t, profil)]


def profils_pareto_optimaux(jeu: Jeu) -> List[Profil]:
    """Tous les profils du jeu qu'aucun autre profil ne domine (définition 2 du cours)."""
    return [p for p in jeu.profils() if not dominants(jeu, p)]


# =============================================================================
# 5. Niveau de sécurité (complément : cours chap. 3 « Pareto versus sécurité », chap. 4)
# =============================================================================

@dataclass
class Securite:
    """Maxmin en stratégies pures.

    garanties_j1[i] = min_j u1(Ai, Bj)   (pire cas de la ligne i)
    garanties_j2[j] = min_i u2(Ai, Bj)   (pire cas de la colonne j)
    """
    garanties_j1: List[Nombre]
    garanties_j2: List[Nombre]
    maxmin_j1: Nombre
    maxmin_j2: Nombre
    prudentes_j1: List[int]
    prudentes_j2: List[int]

    @property
    def profils_prudents(self) -> List[Profil]:
        return [(i, j) for i in self.prudentes_j1 for j in self.prudentes_j2]


def calculer_securite(jeu: Jeu) -> Securite:
    g1 = [min(jeu.A[i]) for i in range(jeu.m)]
    g2 = [min(jeu.B[i][j] for i in range(jeu.m)) for j in range(jeu.n)]
    v1, v2 = max(g1), max(g2)
    return Securite(g1, g2, v1, v2,
                    [i for i, g in enumerate(g1) if _egal(g, v1)],
                    [j for j, g in enumerate(g2) if _egal(g, v2)])


# =============================================================================
# 6. Analyse complète
# =============================================================================

@dataclass
class Analyse:
    jeu: Jeu
    br1: Dict[int, List[int]]            # R1(Bj) pour chaque colonne j
    br2: Dict[int, List[int]]            # R2(Ai) pour chaque ligne i
    ensemble_br1: Set[Profil]
    ensemble_br2: Set[Profil]
    equilibres: List[Profil]             # BR1 inter BR2, trié
    dominants_par_equilibre: Dict[Profil, List[Profil]]  # profils qui dominent chaque NE
    interchangeabilite: Dict[Tuple[Profil, Profil], bool]  # pour chaque paire de NE
    securite: Securite

    @property
    def equilibres_pareto_optimaux(self) -> List[Profil]:
        return [e for e in self.equilibres if not self.dominants_par_equilibre[e]]

    @property
    def equilibres_domines(self) -> List[Profil]:
        return [e for e in self.equilibres if self.dominants_par_equilibre[e]]


def analyser(jeu: Jeu) -> Analyse:
    """Enchaîne R3 (meilleures réponses), R4 (équilibres), R6 (Pareto) + compléments."""
    br1 = meilleures_reponses_j1(jeu)
    br2 = meilleures_reponses_j2(jeu)
    ens1, ens2 = profils_br1(br1), profils_br2(br2)
    equilibres = sorted(ens1 & ens2)
    dominants_ne = {e: dominants(jeu, e) for e in equilibres}
    inter = {(s, t): interchangeables(jeu, s, t)
             for idx, s in enumerate(equilibres) for t in equilibres[idx + 1:]}
    return Analyse(jeu, br1, br2, ens1, ens2, equilibres, dominants_ne, inter,
                   calculer_securite(jeu))


# =============================================================================
# 7. Affichage (R2, R5, R6)
# =============================================================================

def _tableau(coin: str, entetes_col: List[str], entetes_lig: List[str],
             cellules: List[List[str]]) -> str:
    """Dessine un tableau ASCII aligné."""
    w0 = max([len(coin)] + [len(h) for h in entetes_lig])
    ws = [max([len(entetes_col[j])] + [len(cellules[i][j]) for i in range(len(entetes_lig))])
          for j in range(len(entetes_col))]
    sep = "+" + "-" * (w0 + 2) + "".join("+" + "-" * (w + 2) for w in ws) + "+"

    def ligne(premier: str, cases: List[str]) -> str:
        return ("| " + premier.ljust(w0) + " "
                + "".join("| " + c.center(w) + " " for c, w in zip(cases, ws)) + "|")

    sortie = [sep, ligne(coin, entetes_col), sep]
    for i, nom in enumerate(entetes_lig):
        sortie.append(ligne(nom, cellules[i]))
        sortie.append(sep)
    return "\n".join(sortie)


def formater_matrice_gains(jeu: Jeu, matrice: List[List[Nombre]], titre: str) -> str:
    cellules = [[fmt(matrice[i][j]) for j in range(jeu.n)] for i in range(jeu.m)]
    return f"{titre}\n" + _tableau("J1 \\ J2", jeu.noms_j2, jeu.noms_j1, cellules)


def formater_jeu(jeu: Jeu, analyse: Analyse | None = None) -> str:
    """Matrice des couples (u1, u2).

    Si `analyse` est fournie, on marque d'une étoile chaque gain qui correspond à une
    meilleure réponse : une cellule '(26*, 10*)' (deux étoiles) est un équilibre de Nash.
    """
    cellules: List[List[str]] = []
    for i in range(jeu.m):
        ligne = []
        for j in range(jeu.n):
            e1 = e2 = ""
            if analyse is not None:
                e1 = "*" if (i, j) in analyse.ensemble_br1 else ""
                e2 = "*" if (i, j) in analyse.ensemble_br2 else ""
            ligne.append(f"({fmt(jeu.A[i][j])}{e1}, {fmt(jeu.B[i][j])}{e2})")
        cellules.append(ligne)
    return _tableau("J1 \\ J2", jeu.noms_j2, jeu.noms_j1, cellules)


def _liste_profils(jeu: Jeu, profils: Sequence[Profil]) -> str:
    return "{" + ", ".join(jeu.nom_profil(p) for p in profils) + "}"


def _liste_noms(indices: Sequence[int], noms: Sequence[str]) -> str:
    return "{" + ", ".join(noms[i] for i in indices) + "}"


def _gains_txt(jeu: Jeu, profil: Profil) -> str:
    u1, u2 = jeu.gains(profil)
    return f"({fmt(u1)}, {fmt(u2)})"


def formater_meilleures_reponses(a: Analyse) -> str:
    jeu = a.jeu
    lignes = ["Meilleures réponses du joueur 1 (selon la colonne jouée par le joueur 2) :"]
    for j in range(jeu.n):
        gain = jeu.A[a.br1[j][0]][j]
        lignes.append(f"  R1({jeu.nom_j2(j)}) = {_liste_noms(a.br1[j], jeu.noms_j1)}"
                      f"    [u1 max = {fmt(gain)}]")
    lignes.append("Meilleures réponses du joueur 2 (selon la ligne jouée par le joueur 1) :")
    for i in range(jeu.m):
        gain = jeu.B[i][a.br2[i][0]]
        lignes.append(f"  R2({jeu.nom_j1(i)}) = {_liste_noms(a.br2[i], jeu.noms_j2)}"
                      f"    [u2 max = {fmt(gain)}]")
    lignes.append(f"BR1 = {_liste_profils(jeu, sorted(a.ensemble_br1))}")
    lignes.append(f"BR2 = {_liste_profils(jeu, sorted(a.ensemble_br2))}")
    return "\n".join(lignes)


def formater_equilibres(a: Analyse) -> str:
    if not a.equilibres:
        return ("Aucun équilibre de Nash en stratégies pures : BR1 inter BR2 est vide.\n"
                "(Un équilibre en stratégies mixtes existe toujours, mais il sort du cadre de ce TP.)")
    lignes = [f"Équilibres de Nash en stratégies pures (BR1 inter BR2) : {len(a.equilibres)}"]
    for e in a.equilibres:
        lignes.append(f"  {a.jeu.nom_profil(e)}  ->  gains {_gains_txt(a.jeu, e)}")
    return "\n".join(lignes)


def formater_pareto(a: Analyse) -> str:
    if not a.equilibres:
        return "Analyse de Pareto : sans objet (aucun équilibre de Nash pur)."
    jeu = a.jeu
    lignes = ["Optimalité de Pareto des équilibres de Nash :"]
    for e in a.equilibres:
        entete = f"  {jeu.nom_profil(e)} {_gains_txt(jeu, e)}"
        doms = a.dominants_par_equilibre[e]
        if not doms:
            lignes.append(f"{entete} : Pareto-optimal")
        else:
            details = ", ".join(
                f"{jeu.nom_profil(d)}={_gains_txt(jeu, d)}{' [NE]' if d in a.equilibres else ''}"
                for d in doms)
            lignes.append(f"{entete} : DOMINÉ au sens de Pareto par {details}")
    lignes.append(f"  -> NE Pareto-optimaux : {_liste_profils(jeu, a.equilibres_pareto_optimaux)}")
    lignes.append(f"  -> NE dominés         : {_liste_profils(jeu, a.equilibres_domines)}")
    lignes.append("Profils Pareto-optimaux du jeu (tous profils confondus) : "
                  + _liste_profils(jeu, profils_pareto_optimaux(jeu)))
    return "\n".join(lignes)


def formater_interchangeabilite(a: Analyse) -> str:
    if len(a.equilibres) < 2:
        return "Interchangeabilité : sans objet (moins de deux équilibres)."
    jeu = a.jeu
    lignes = ["Interchangeabilité des équilibres (cours, chap. 3) :"]
    for (s, t), oui in a.interchangeabilite.items():
        if oui:
            verdict = "interchangeables"
        else:
            (i, j), (k, l) = s, t
            manquants = [p for p in ((i, l), (k, j)) if not est_equilibre_nash(jeu, p)]
            verdict = ("NON interchangeables (profils croisés qui ne sont pas des NE : "
                       + ", ".join(jeu.nom_profil(p) for p in manquants) + ")")
        lignes.append(f"  {jeu.nom_profil(s)} et {jeu.nom_profil(t)} : {verdict}")
    return "\n".join(lignes)


def formater_securite(a: Analyse) -> str:
    jeu, sec = a.jeu, a.securite
    lignes = ["Niveau de sécurité (maxmin en stratégies pures, cours chap. 3 et 4) :"]
    g1 = ", ".join(f"{jeu.nom_j1(i)}={fmt(g)}" for i, g in enumerate(sec.garanties_j1))
    g2 = ", ".join(f"{jeu.nom_j2(j)}={fmt(g)}" for j, g in enumerate(sec.garanties_j2))
    lignes.append(f"  Joueur 1 : pire gain de chaque ligne   {g1}")
    lignes.append(f"             v1 = {fmt(sec.maxmin_j1)}, stratégie(s) prudente(s) "
                  f"{_liste_noms(sec.prudentes_j1, jeu.noms_j1)}")
    lignes.append(f"  Joueur 2 : pire gain de chaque colonne {g2}")
    lignes.append(f"             v2 = {fmt(sec.maxmin_j2)}, stratégie(s) prudente(s) "
                  f"{_liste_noms(sec.prudentes_j2, jeu.noms_j2)}")
    lignes.append("  Profil(s) prudent(s) (maxmin) :")
    for p in sec.profils_prudents:
        ne = "OUI" if p in a.equilibres else "non"
        lignes.append(f"    {jeu.nom_profil(p)} gains {_gains_txt(jeu, p)} -> équilibre de Nash : {ne}")
    if a.equilibres:
        lignes.append("  Garantie offerte par les stratégies de chaque équilibre de Nash :")
        for e in a.equilibres:
            i, j = e
            prudent = "oui" if (i in sec.prudentes_j1 and j in sec.prudentes_j2) else "non"
            lignes.append(f"    {jeu.nom_profil(e)} {_gains_txt(jeu, e)} : garantie J1 = "
                          f"{fmt(sec.garanties_j1[i])} (v1 = {fmt(sec.maxmin_j1)}), garantie J2 = "
                          f"{fmt(sec.garanties_j2[j])} (v2 = {fmt(sec.maxmin_j2)}), profil prudent : {prudent}")
    return "\n".join(lignes)


def rapport_complet(jeu: Jeu, complements: bool = True) -> str:
    """Rapport texte complet : R2 + R3 + R4/R5 + R6 (+ compléments du cours)."""
    a = analyser(jeu)
    barre = "=" * 72
    parties = [
        barre,
        f"JEU : {jeu.nom}   ({jeu.m} stratégies pour J1 x {jeu.n} stratégies pour J2)",
        barre,
        formater_matrice_gains(jeu, jeu.A, "Matrice A (gains du joueur 1) :"),
        "",
        formater_matrice_gains(jeu, jeu.B, "Matrice B (gains du joueur 2) :"),
        "",
        "Matrice des couples (u1, u2) :",
        formater_jeu(jeu),
        "",
        formater_meilleures_reponses(a),
        "",
        "Matrice annotée (* = gain d'une meilleure réponse ; deux * = équilibre de Nash) :",
        formater_jeu(jeu, a),
        "",
        formater_equilibres(a),
        "",
        formater_pareto(a),
    ]
    if complements:
        parties += ["", "--- Compléments du cours ---", formater_interchangeabilite(a),
                    "", formater_securite(a)]
    return "\n".join(parties)


# =============================================================================
# 8. Jeux d'essai du cours (R7)
# =============================================================================

def _grille(texte: str) -> Tuple[Tuple[Tuple[Nombre, Nombre], ...], ...]:
    """Une ligne de texte par stratégie du joueur 1 ; couples '(u1, u2)' recopiés des slides."""
    grille = []
    for ligne in (x.strip() for x in texte.strip().splitlines()):
        if ligne:
            nb = extraire_nombres(ligne)
            grille.append(tuple((nb[k], nb[k + 1]) for k in range(0, len(nb), 2)))
    return tuple(grille)


@dataclass(frozen=True)
class Exemple:
    cle: str
    source: str                               # où l'exemple apparaît dans le cours
    description: str
    grille: str                               # couples de gains, une ligne par stratégie de J1
    equilibres_attendus: Tuple[Profil, ...]   # indices à partir de 0
    domines_attendus: Tuple[Profil, ...]      # parmi les NE : ceux dominés au sens de Pareto
    noms_j1: Optional[Tuple[str, ...]] = None
    noms_j2: Optional[Tuple[str, ...]] = None

    def jeu(self) -> Jeu:
        return jeu_depuis_couples(
            _grille(self.grille), nom=f"{self.cle} - {self.description}",
            noms_j1=list(self.noms_j1) if self.noms_j1 else None,
            noms_j2=list(self.noms_j2) if self.noms_j2 else None)


# Jeu « choix d'un chiffre » (chap. 3, optimum de Pareto, exemple 1) : généré, 10 x 10.
_GRILLE_CHIFFRE = "\n".join(
    " ".join(f"({10 * a}, {10 * a})" if a == b else "(0, 0)" for b in range(1, 11))
    for a in range(1, 11))
_CHIFFRES = tuple(str(k) for k in range(1, 11))

EXEMPLES: Dict[str, Exemple] = {e.cle: e for e in [
    Exemple(
        "sujet", "TP 2 §3 = chap. 3, exercice 2 (André et Betsy)",
        "4x4 : 2 NE, meilleures réponses multiples pour J2, un NE dominé",
        """(26, 10) (10, 2) (30, 8) (14, 0)
           (2, 2)   (2, 2)  (22, 8) (22, 8)
           (24, 8)  (8, 0)  (28, 8) (8, 2)
           (4, 0)   (0, 10) (20, 8) (16, 10)""",
        ((0, 0), (1, 3)), ((1, 3),)),
    Exemple(
        "ex3_1", "chap. 3, exemple 3.1",
        "2 NE : (B,G) Pareto-optimal et (H,D) dominé par (B,G)",
        """(0, 0)   (2, 2)
           (10, 11) (-1, 0)""",
        ((0, 1), (1, 0)), ((0, 1),), ("H", "B"), ("G", "D")),
    Exemple(
        "ex3_2", "chap. 3, exemple 3.2",
        "3x3 : un seul NE (B,R), Pareto-optimal ; la dominance du chap. 2 ne permet pas de conclure",
        """(0, 6) (6, 0) (4, 3)
           (6, 0) (0, 6) (4, 3)
           (3, 3) (3, 3) (5, 5)""",
        ((2, 2),), (), ("T", "M", "B"), ("L", "M", "R")),
    Exemple(
        "ex3_3", "chap. 3, exemple 3.3",
        "3x3 : un seul NE (A2,B3), dominé au sens de Pareto",
        """(6, 7) (9, 6) (0, 6)
           (5, 2) (8, 2) (4, 5)
           (7, 7) (7, 8) (0, 9)""",
        ((1, 2),), ((1, 2),)),
    Exemple(
        "ex3_4", "chap. 3, exemple 3.4",
        "ex æquo pour J1 (R1(G)={H,B}) ; la dominance faible écarterait le NE (B,G)",
        """(10, 0)  (5, 2)
           (10, 11) (2, 0)""",
        ((0, 1), (1, 0)), ((0, 1),), ("H", "B"), ("G", "D")),
    Exemple(
        "carrefour", "chap. 3, jeux célèbres : jeu du carrefour",
        "2 NE (P,S) et (S,P), tous deux Pareto-optimaux, non interchangeables",
        """(-1, -1) (2, 1)
           (1, 2)  (0, 0)""",
        ((0, 1), (1, 0)), (), ("P", "S"), ("P", "S")),
    Exemple(
        "pierre_feuille_ciseaux", "chap. 3, jeux célèbres : Pierre, Feuille, Ciseaux",
        "3x3 cyclique : aucun NE pur",
        """(0, 0)  (-1, 1) (1, -1)
           (1, -1) (0, 0)  (-1, 1)
           (-1, 1) (1, -1) (0, 0)""",
        (), (), ("Pierre", "Feuille", "Ciseaux"), ("Pierre", "Feuille", "Ciseaux")),
    Exemple(
        "bataille_couple", "chap. 3, jeux célèbres : la bataille du couple",
        "2 NE (Théâtre,Théâtre) et (Foot,Foot), tous deux Pareto-optimaux",
        """(3, 1) (0, 0)
           (0, 0) (1, 3)""",
        ((0, 0), (1, 1)), (), ("Théâtre", "Foot"), ("Théâtre", "Foot")),
    Exemple(
        "tir_au_but", "chap. 3, extension mixte : tir au but",
        "2x2 : aucun NE pur (il faudra des stratégies mixtes)",
        """(0, 1) (1, 0)
           (1, 0) (0, 1)""",
        (), (), ("Tg", "Td"), ("Sg", "Sd")),
    Exemple(
        "dell_compaq", "chap. 3, exercice 1 (Dell et Compaq)",
        "2x4 : 3 NE, ex æquo pour les deux joueurs, tous Pareto-optimaux",
        """(600, 200) (600, 200) (100, 100) (100, 100)
           (200, 600) (100, 100) (100, 100) (200, 600)""",
        ((0, 0), (0, 1), (1, 3)), (), ("W", "L"), ("A", "B", "C", "D")),
    Exemple(
        "chiffre", "chap. 3, optimum de Pareto, exemple 1 (choix d'un chiffre)",
        "10x10 : 10 NE (a,a) ; seul (10,10) de gains (100,100) est Pareto-optimal",
        _GRILLE_CHIFFRE,
        tuple((k, k) for k in range(10)), tuple((k, k) for k in range(9)),
        _CHIFFRES, _CHIFFRES),
    Exemple(
        "securite", "chap. 3, Pareto versus niveau de sécurité, exemple 2",
        "NE (U,U) Pareto-optimal mais garantie 0 ; (V,V) dominé mais garantie 7",
        """(9, 9) (0, 8)
           (8, 0) (7, 7)""",
        ((0, 0), (1, 1)), ((1, 1),), ("U", "V"), ("U", "V")),
    Exemple(
        "dilemme", "chap. 2, dilemme du prisonnier",
        "1 seul NE (Avoue,Avoue), dominé par (N'avoue pas,N'avoue pas)",
        """(-5, -5)  (0, -10)
           (-10, 0)  (-1, -1)""",
        ((0, 0),), ((0, 0),), ("Avoue", "N'avoue pas"), ("Avoue", "N'avoue pas")),
    Exemple(
        "essd_chap2", "chap. 2, équilibre itératif en stratégies strictement dominantes",
        "3x3 : (H,G) obtenu par ESSD est l'unique NE (prop. 3.1), mais il est dominé",
        """(4, 3) (5, 1) (6, 2)
           (2, 1) (8, 4) (3, 6)
           (3, 0) (9, 6) (2, 8)""",
        ((0, 0),), ((0, 0),), ("H", "M", "B"), ("G", "M", "D")),
    Exemple(
        "dominance_faible_chap2", "chap. 2, ordre d'élimination des stratégies faiblement dominées",
        "4 NE ; l'élimination faible ne retrouve que (M,L) ou (M,R) selon l'ordre",
        """(1, 2) (2, 3) (0, 3)
           (2, 2) (2, 1) (3, 2)
           (2, 1) (0, 0) (1, 0)""",
        ((0, 1), (1, 0), (1, 2), (2, 0)), ((1, 0), (2, 0)), ("T", "M", "B"), ("L", "C", "R")),
    Exemple(
        "poule_mouillee", "chap. 4, équilibre de Nash versus équilibre maxmin (poule mouillée)",
        "2 NE (C,D) et (D,C) ; le profil maxmin (D,D) n'est PAS un NE",
        """(-100, -100) (10, -10)
           (-10, 10)   (0, 0)""",
        ((0, 1), (1, 0)), (),
        ("Continuer", "Dévier"), ("Continuer", "Dévier")),
    Exemple(
        "maxmin_chap4", "chap. 4, paiement maxmin (v1 = 2, v2 = 1)",
        "3x2 : profil maxmin (T,L) de gains (3,1) ; unique NE (B,R) de gains (3,3)",
        """(3, 1)    (2, 2)
           (0, 8)    (0, -1)
           (-100, 2) (3, 3)""",
        ((2, 1),), (), ("T", "M", "B"), ("L", "R")),
    Exemple(
        "maxmin_multiple", "chap. 4, plusieurs stratégies maxmin",
        "2x2 : J2 a deux stratégies maxmin, donc deux profils prudents (2,3) et (1,1) ; aucun NE pur",
        """(3, 1) (0, 4)
           (2, 3) (1, 1)""",
        (), (), ("T", "B"), ("L", "R")),
]}


# =============================================================================
# 9. Interface graphique (Tkinter) : les étapes du cours, animées
# =============================================================================
#
# Le moteur découpe l'analyse en ÉTAPES (construire_etapes), comme on la fait à la main :
#   1. J1 examine chaque colonne  -> ses meilleures réponses R1(Bj)
#   2. J2 examine chaque ligne    -> ses meilleures réponses R2(Ai)
#   3. intersection BR1 inter BR2 -> équilibres de Nash
#   4. un équilibre après l'autre -> optimalité de Pareto
# L'interface ne fait que montrer ces étapes (▶ lecture, ⏭ pas à pas, ⏮ retour, ↺ début).

@dataclass(frozen=True)
class Etape:
    """Un état d'affichage : tout ce qui est visible à ce moment de l'analyse."""
    texte: str                                        # message de la barre d'état
    log: str = ""                                     # ligne ajoutée au journal
    br1: FrozenSet[Profil] = frozenset()              # meilleures réponses de J1 révélées
    br2: FrozenSet[Profil] = frozenset()              # meilleures réponses de J2 révélées
    ne: FrozenSet[Profil] = frozenset()               # équilibres de Nash révélés
    colonne: Optional[int] = None                     # colonne examinée par J1 à cette étape
    ligne: Optional[int] = None                       # ligne examinée par J2 à cette étape
    pareto: Optional[Profil] = None                   # équilibre dont on étudie la dominance
    dominants: Tuple[Profil, ...] = ()                # profils qui le dominent
    verdicts: Tuple[Tuple[Profil, bool], ...] = ()    # (équilibre, est Pareto-optimal ?) établis


def _abrege_profils(jeu: Jeu, profils: Sequence[Profil], limite: int = 4) -> str:
    texte = ", ".join(f"{jeu.nom_profil(p)}={_gains_txt(jeu, p)}" for p in profils[:limite])
    if len(profils) > limite:
        texte += f", … (+{len(profils) - limite})"
    return texte


def construire_etapes(a: Analyse, intro: str = "") -> List[Etape]:
    """Liste ordonnée des états d'affichage ; l'étape 0 est le jeu seul, sans marque."""
    jeu = a.jeu
    etapes = [Etape((intro or jeu.nom) + "  ·  appuyez sur ▶ ou ⏭ pour lancer l'analyse")]

    br1: Set[Profil] = set()
    for j in range(jeu.n):
        br1 |= {(i, j) for i in a.br1[j]}
        texte = (f"J1 examine la colonne {jeu.nom_j2(j)} : R1({jeu.nom_j2(j)}) = "
                 f"{_liste_noms(a.br1[j], jeu.noms_j1)}   (u1 max = {fmt(jeu.A[a.br1[j][0]][j])})")
        etapes.append(Etape(texte, texte, frozenset(br1), colonne=j))

    br2: Set[Profil] = set()
    pleine1 = frozenset(br1)
    for i in range(jeu.m):
        br2 |= {(i, j) for j in a.br2[i]}
        texte = (f"J2 examine la ligne {jeu.nom_j1(i)} : R2({jeu.nom_j1(i)}) = "
                 f"{_liste_noms(a.br2[i], jeu.noms_j2)}   (u2 max = {fmt(jeu.B[i][a.br2[i][0]])})")
        etapes.append(Etape(texte, texte, pleine1, frozenset(br2), ligne=i))

    pleine2, ne = frozenset(br2), frozenset(a.equilibres)
    if a.equilibres:
        liste = ", ".join(f"{jeu.nom_profil(e)} {_gains_txt(jeu, e)}" for e in a.equilibres)
        texte = f"BR1 ∩ BR2 : {len(ne)} équilibre(s) de Nash  →  {liste}"
    else:
        texte = "BR1 ∩ BR2 = ∅ : aucun équilibre de Nash en stratégies pures"
    etapes.append(Etape(texte, texte, pleine1, pleine2, ne))

    verdicts: List[Tuple[Profil, bool]] = []
    for e in a.equilibres:
        doms = a.dominants_par_equilibre[e]
        verdicts.append((e, not doms))
        if doms:
            texte = (f"{jeu.nom_profil(e)} {_gains_txt(jeu, e)} est DOMINÉ au sens de Pareto par "
                     f"{_abrege_profils(jeu, doms)}")
        else:
            texte = (f"{jeu.nom_profil(e)} {_gains_txt(jeu, e)} est Pareto-optimal : "
                     f"aucun profil ne le domine")
        etapes.append(Etape(texte, texte, pleine1, pleine2, ne, pareto=e,
                            dominants=tuple(doms), verdicts=tuple(verdicts)))
    if a.equilibres:
        texte = (f"✔ Bilan : {len(ne)} équilibre(s) de Nash, "
                 f"{len(a.equilibres_pareto_optimaux)} Pareto-optimal(aux), "
                 f"{len(a.equilibres_domines)} dominé(s)")
        etapes.append(Etape(texte, texte, pleine1, pleine2, ne, verdicts=tuple(verdicts)))
    return etapes


def groupe_exemple(ex: Exemple) -> str:
    """Rubrique du menu des exemples : 'TP 2 (sujet)', 'Chapitre 2', 'Chapitre 3', ..."""
    if ex.source.startswith("TP"):
        return "TP 2 (sujet)"
    chapitre = re.search(r"chap\. (\d)", ex.source)
    return f"Chapitre {chapitre.group(1)}" if chapitre else "Autres"


def selftest() -> bool:
    """Vérifie en console tous les exemples du cours (sans interface graphique)."""
    tout_ok = True
    for cle, ex in EXEMPLES.items():
        jeu = ex.jeu()
        a = analyser(jeu)
        etapes = construire_etapes(a)
        ok = (a.equilibres == sorted(ex.equilibres_attendus)
              and a.equilibres_domines == sorted(ex.domines_attendus)
              and all(est_equilibre_nash(jeu, e) for e in a.equilibres)
              and sorted(etapes[-1].ne) == a.equilibres)
        tout_ok &= ok
        liste = ", ".join(jeu.nom_profil(e) for e in a.equilibres) or "aucun NE pur"
        print(("OK " if ok else "KO "), f"{cle:<24}", "->", liste)
    print("TOUS LES TESTS PASSENT" if tout_ok else "ECHEC")
    return tout_ok


# ---- palette (même thème sombre que le TP de dominance) ----------------------
BG, CARD, CARD2 = "#0f172a", "#1e293b", "#334155"
TXT, MUTED = "#f1f5f9", "#94a3b8"
ACCENT, RED, GREEN, GOLD = "#6366f1", "#f43f5e", "#22c55e", "#fbbf24"
J1C, J2C = "#6366f1", "#06b6d4"   # couleurs des meilleures réponses de J1 (indigo) et J2 (cyan)


def blend(c1: str, c2: str, t: float) -> str:
    """Mélange de deux couleurs '#rrggbb' : t=0 -> c1, t=1 -> c2."""
    t = max(0.0, min(1.0, t))
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def rrect(c, x1, y1, x2, y2, r, **kw):
    """Rectangle aux coins arrondis sur un Canvas Tkinter."""
    r = max(0, min(r, (x2 - x1) / 2, (y2 - y1) / 2))
    pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
           x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
    return c.create_polygon(pts, smooth=True, **kw)


if HAS_TK:

    class Btn(tk.Label):
        """Bouton plat avec effet de survol."""

        def __init__(self, parent, text, cmd, color=CARD2):
            super().__init__(parent, text=text, bg=color, fg=TXT, padx=14, pady=8,
                             font=("Helvetica", 11, "bold"), cursor="hand2")
            self.color, self.cmd = color, cmd
            self.bind("<Button-1>", lambda e: self.cmd())
            self.bind("<Enter>", lambda e: self.configure(bg=blend(self.color, "#ffffff", 0.15)))
            self.bind("<Leave>", lambda e: self.configure(bg=self.color))

        def set(self, text=None, color=None):
            if text:
                self.configure(text=text)
            if color:
                self.color = color
                self.configure(bg=color)

    class App(tk.Tk):
        def __init__(self):
            super().__init__()
            self.title("Équilibre de Nash : stratégies pures et Pareto")
            self.geometry("1100x720")
            self.minsize(960, 580)
            self.configure(bg=BG)
            self.perso: List[Tuple[str, Jeu]] = []        # jeux saisis / chargés par l'utilisateur
            self.jeu: Jeu = EXEMPLES["sujet"].jeu()
            self.analyse: Analyse = analyser(self.jeu)
            self.etapes: List[Etape] = []
            self.idx = 0
            self.busy = self.playing = False
            self._jeton = 0                                # invalide les animations en cours
            self._fonts: Dict[Tuple[int, str], tkfont.Font] = {}
            self._build()
            self.charger_exemple("sujet")

        # ---------------- interface ----------------
        @staticmethod
        def _style_menu():
            return dict(bg=CARD, fg=TXT, activebackground=ACCENT, activeforeground="white",
                        relief="flat", font=("Helvetica", 11))

        def _build(self):
            top = tk.Frame(self, bg=BG)
            top.pack(fill="x", padx=20, pady=(16, 8))
            tk.Label(top, text="Équilibre de Nash", bg=BG, fg=TXT,
                     font=("Helvetica", 20, "bold")).pack(side="left")
            tk.Label(top, text="  stratégies pures · Pareto", bg=BG, fg=MUTED,
                     font=("Helvetica", 14)).pack(side="left")

            bar = tk.Frame(self, bg=BG)
            bar.pack(fill="x", padx=20, pady=(0, 8))
            self.gvar = tk.StringVar()
            self.menu_btn = tk.Menubutton(bar, textvariable=self.gvar, bg=CARD, fg=TXT,
                                          activebackground=CARD2, activeforeground=TXT,
                                          relief="flat", padx=14, pady=8, width=38, anchor="w",
                                          font=("Helvetica", 11, "bold"), cursor="hand2")
            self.menu = tk.Menu(self.menu_btn, tearoff=0, **self._style_menu())
            self.menu_btn.configure(menu=self.menu)
            self.menu_btn.pack(side="left")
            Btn(bar, "📄  Rapport", self.show_report).pack(side="left", padx=14)

            self.b_play = Btn(bar, "▶  Lecture", self.on_play, ACCENT)
            for w in (Btn(bar, "⏩", self.fin), Btn(bar, "⏭", self.step)):
                w.pack(side="right", padx=2)
            self.b_play.pack(side="right", padx=2)
            for w in (Btn(bar, "⏮", self.undo), Btn(bar, "↺", self.reset)):
                w.pack(side="right", padx=2)
            self.speed = tk.Scale(bar, from_=1, to=5, orient="horizontal", showvalue=False,
                                  length=90, bg=BG, troughcolor=CARD, highlightthickness=0, fg=TXT)
            self.speed.set(3)
            self.speed.pack(side="right", padx=(0, 6))
            tk.Label(bar, text="vitesse", bg=BG, fg=MUTED).pack(side="right")

            legende = tk.Frame(self, bg=BG)
            legende.pack(fill="x", padx=20, pady=(0, 4))
            for couleur, texte in ((J1C, "meilleure réponse de J1 (u1)"),
                                   (J2C, "meilleure réponse de J2 (u2)"),
                                   (GOLD, "équilibre de Nash"),
                                   (GREEN, "Pareto-optimal / dominant"), (RED, "dominé")):
                tk.Label(legende, bg=couleur, width=2).pack(side="left", padx=(0, 5))
                tk.Label(legende, text=texte, bg=BG, fg=MUTED,
                         font=("Helvetica", 10)).pack(side="left", padx=(0, 16))

            self.canvas = tk.Canvas(self, bg=BG, highlightthickness=0)
            self.canvas.pack(fill="both", expand=True, padx=20)
            self.canvas.bind("<Configure>", self._on_resize)

            self.status = tk.Label(self, bg=CARD, fg=TXT, anchor="w", justify="left", padx=16,
                                   pady=10, font=("Helvetica", 12, "bold"))
            self.status.pack(fill="x", padx=20, pady=(8, 0))
            self.log = tk.Text(self, height=5, bg=BG, fg=MUTED, relief="flat",
                               font=("Courier", 10), padx=16, pady=6, highlightthickness=0,
                               state="disabled")
            self.log.pack(fill="x", padx=20, pady=(0, 12))

            self.bind("<Right>", lambda e: self.step())
            self.bind("<Left>", lambda e: self.undo())
            self.bind("<space>", lambda e: self.on_play())

        def _on_resize(self, event):
            self.status.configure(wraplength=max(200, event.width - 40))
            if not self.busy:
                self.redraw()

        def _fill_menu(self):
            self.menu.delete(0, "end")
            groupes: Dict[str, List[Exemple]] = {}
            for ex in EXEMPLES.values():
                groupes.setdefault(groupe_exemple(ex), []).append(ex)
            for nom in sorted(groupes, key=lambda g: (not g.startswith("TP"), g)):
                sous = tk.Menu(self.menu, tearoff=0, **self._style_menu())
                for ex in groupes[nom]:
                    sous.add_command(label=ex.source, command=lambda c=ex.cle: self.charger_exemple(c))
                self.menu.add_cascade(label=nom, menu=sous)
            if self.perso:
                sous = tk.Menu(self.menu, tearoff=0, **self._style_menu())
                for titre, jeu in self.perso:
                    sous.add_command(label=titre, command=lambda t=titre, j=jeu: self.charger(j, t))
                self.menu.add_cascade(label="Mes jeux", menu=sous)
            self.menu.add_separator()
            self.menu.add_command(label="＋  Saisir une matrice…", command=self.new_matrix)
            self.menu.add_command(label="＋  Jeu aléatoire…", command=self.new_random)
            self.menu.add_command(label="＋  Charger un fichier…", command=self.new_file)
            self.menu.add_command(label="💾  Enregistrer ce jeu…", command=self.save_game)

        # ---------------- état ----------------
        def charger_exemple(self, cle):
            ex = EXEMPLES[cle]
            self.charger(ex.jeu(), ex.source, ex.description)

        def charger(self, jeu, titre, description=""):
            self.jeu, self.analyse = jeu, analyser(jeu)
            self.etapes = construire_etapes(self.analyse, description or jeu.nom)
            self.gvar.set(titre if len(titre) <= 38 else titre[:37] + "…")
            self._fill_menu()
            self.aller_a(0)

        def aller_a(self, k):
            """Saute directement à l'étape k (sans animation) et annule toute animation en cours."""
            self._jeton += 1
            self.busy = self.playing = False
            self.b_play.set("▶  Lecture")
            self.idx = max(0, min(k, len(self.etapes) - 1))
            self.log.configure(state="normal")
            self.log.delete("1.0", "end")
            self.log.configure(state="disabled")
            for n in range(1, self.idx + 1):
                self.write(f"Étape {n} : {self.etapes[n].log}")
            self.show_status()
            self.redraw()

        def reset(self):
            self.aller_a(0)

        def fin(self):
            self.aller_a(len(self.etapes) - 1)

        def show_status(self):
            fini = self.idx == len(self.etapes) - 1
            self.status.configure(text=self.etapes[self.idx].texte,
                                  fg=GOLD if fini and self.analyse.equilibres else TXT)

        def write(self, text):
            self.log.configure(state="normal")
            self.log.insert("end", text + "\n")
            self.log.see("end")
            self.log.configure(state="disabled")

        # ---------------- actions ----------------
        def step(self, done=None):
            if self.busy or self.idx >= len(self.etapes) - 1:
                self.playing = False
                self.b_play.set("▶  Lecture")
                return
            self.animate(self.idx + 1, done)

        def undo(self):
            if not self.busy and self.idx > 0:
                self.aller_a(self.idx - 1)

        def on_play(self):
            if self.playing:
                self.playing = False
                self.b_play.set("▶  Lecture")
                return
            if self.busy:
                return
            if self.idx >= len(self.etapes) - 1:
                self.aller_a(0)
            self.playing = True
            self.b_play.set("⏸  Pause")
            self._auto()

        def _auto(self):
            if not self.playing:
                return
            if self.busy:
                self.after(100, self._auto)
            elif self.idx >= len(self.etapes) - 1:
                self.playing = False
                self.b_play.set("▶  Lecture")
            else:
                self.step(lambda: self.after(int(500 / self.speed.get()), self._auto))

        def animate(self, k, done):
            """Étape idx -> k : la ligne/colonne examinée clignote, puis les marques apparaissent."""
            jeton = self._jeton
            prev, cible = self.etapes[k - 1], self.etapes[k]
            self.busy = True
            ms = 1500 / self.speed.get()
            n1, n2 = max(5, int(ms * 0.55 / 33)), max(4, int(ms * 0.45 / 33))
            self.status.configure(text=cible.texte, fg=TXT)

            def phase1(i):
                if jeton != self._jeton:
                    return
                self.redraw(prev, focus=cible, k=0.55 + 0.45 * math.sin(i * 0.5))
                self.after(33, lambda: phase1(i + 1)) if i < n1 else phase2(0)

            def phase2(i):
                if jeton != self._jeton:
                    return
                t = i / n2
                e = t * t * (3 - 2 * t)
                self.redraw(cible, prev=prev, t=e, focus=cible, k=1 - 0.55 * e)
                self.after(33, lambda: phase2(i + 1)) if i < n2 else fin_anim()

            def fin_anim():
                if jeton != self._jeton:
                    return
                self.busy = False
                self.idx = k
                self.write(f"Étape {k} : {cible.log}")
                self.show_status()
                self.redraw()
                if done and self.idx < len(self.etapes) - 1:
                    done()
                else:
                    self.playing = False
                    self.b_play.set("▶  Lecture")

            phase1(0)

        # ---------------- dessin ----------------
        def font(self, size, weight="normal"):
            key = (max(6, int(size)), weight)
            if key not in self._fonts:
                self._fonts[key] = tkfont.Font(family="Helvetica", size=key[0], weight=weight)
            return self._fonts[key]

        def fit(self, text, size, w, weight="normal"):
            f = self.font(size, weight)
            while f.measure(text) > w and size > 6:
                size -= 1
                f = self.font(size, weight)
            return f

        def redraw(self, e=None, prev=None, t=1.0, focus=None, k=None):
            """Dessine la matrice.

            e      : étape dont on dessine les marques (par défaut l'étape courante)
            prev   : étape précédente ; les marques nouvelles de `e` apparaissent avec le fondu t
            focus  : étape dont la ligne / colonne / dominance est mise en valeur (clignote avec k)
            """
            c = self.canvas
            c.delete("all")
            W, H = c.winfo_width(), c.winfo_height()
            if W < 80 or H < 80 or not self.etapes:
                return
            e = e or self.etapes[self.idx]
            focus = focus or e
            k = 0.45 if k is None else k
            jeu = self.jeu
            m, n = jeu.m, jeu.n
            RW, CW, HH, RH = 1.9, 2.7, 0.9, 1.15            # largeur/hauteur en unités u
            u = min((W - 8) / (RW + CW * n), (H - 8) / (HH + RH * m))
            u = max(9.0, min(u, 56.0))
            cw, ch = u * CW, u * RH
            x0 = max(0.0, (W - u * (RW + CW * n)) / 2)
            y0 = max(0.0, (H - u * (HH + RH * m)) / 2)
            gx, gy = x0 + u * RW, y0 + u * HH               # coin haut-gauche des cases
            fs, pad = u * 0.34, max(1.5, u * 0.05)

            # --- en-têtes ---
            coin = "J1 ↓   J2 →"
            c.create_text(x0 + u * RW / 2, y0 + u * HH / 2, text=coin, fill=MUTED,
                          font=self.fit(coin, fs * 0.9, u * RW - 6))
            for j in range(n):
                col = blend(CARD2, J1C, 0.7 * k) if focus.colonne == j else CARD2
                x = gx + j * cw
                rrect(c, x + pad, y0, x + cw - pad, y0 + u * HH - pad, u * 0.15, fill=col, outline="")
                c.create_text(x + cw / 2, y0 + u * HH / 2, text=jeu.nom_j2(j), fill=TXT,
                              font=self.fit(jeu.nom_j2(j), fs * 1.05, cw - 10, "bold"))
            for i in range(m):
                col = blend(CARD2, J2C, 0.7 * k) if focus.ligne == i else CARD2
                y = gy + i * ch
                rrect(c, x0, y + pad, x0 + u * RW - pad, y + ch - pad, u * 0.15, fill=col, outline="")
                c.create_text(x0 + u * RW / 2, y + ch / 2, text=jeu.nom_j1(i), fill=TXT,
                              font=self.fit(jeu.nom_j1(i), fs * 1.05, u * RW - 8, "bold"))

            # --- cases ---
            verdicts = dict(e.verdicts)
            anciens_verdicts = dict(prev.verdicts) if prev else verdicts
            for i in range(m):
                for j in range(n):
                    cell = (i, j)
                    x, y = gx + j * cw, gy + i * ch
                    # fond : or pour un équilibre, assombri pour les autres une fois les NE connus
                    if e.ne:
                        a_ne = 1.0 if (prev is None or cell in prev.ne) else t
                        assombri = 1.0 if (prev is None or prev.ne) else t
                        base = blend(CARD, GOLD, a_ne) if cell in e.ne else blend(CARD, BG, 0.4 * assombri)
                    else:
                        base = CARD
                    if focus.colonne == j:
                        base = blend(base, J1C, 0.22 * k)
                    if focus.ligne == i:
                        base = blend(base, J2C, 0.22 * k)
                    anneau, epaisseur = "", 1
                    if focus.pareto is not None:
                        if cell in focus.dominants:
                            base = blend(base, GREEN, 0.45 * k)
                            anneau, epaisseur = GREEN, max(2.0, u * 0.05)
                        if cell == focus.pareto:
                            anneau, epaisseur = (RED if focus.dominants else GREEN), max(2.5, u * 0.07)
                    rrect(c, x + pad, y + pad, x + cw - pad, y + ch - pad, u * 0.15,
                          fill=base, outline=anneau, width=epaisseur)

                    # valeurs u1 | u2, avec une pastille si c'est une meilleure réponse
                    or_visible = cell in e.ne and (prev is None or cell in prev.ne or t > 0.5)
                    encre = "#0f172a" if or_visible else TXT
                    badge = cell in verdicts and u >= 18
                    vy = y + ch * (0.38 if badge else 0.5)
                    v1, v2 = fmt(jeu.A[i][j]), fmt(jeu.B[i][j])
                    f = self.fit(max(v1, v2, key=len), fs, cw * 0.36, "bold")
                    ph = fs * 1.8
                    for val, px, mine, old, couleur in (
                            (v1, x + cw * 0.27, e.br1, prev.br1 if prev else e.br1, J1C),
                            (v2, x + cw * 0.73, e.br2, prev.br2 if prev else e.br2, J2C)):
                        alpha = (1.0 if cell in old else t) if cell in mine else 0.0
                        if alpha > 0.02:
                            pw = f.measure(val) + fs * 1.1
                            rrect(c, px - pw / 2, vy - ph / 2, px + pw / 2, vy + ph / 2, ph / 2,
                                  fill=blend(base, couleur, alpha), outline="")
                        c.create_text(px, vy, text=val, fill="#ffffff" if alpha > 0.5 else encre, font=f)
                    c.create_line(x + cw * 0.5, vy - ph * 0.35, x + cw * 0.5, vy + ph * 0.35,
                                  fill=blend(base, encre, 0.3))
                    if badge:
                        optimal = verdicts[cell]
                        texte = "✔ Pareto" if optimal else "✖ dominé"
                        alpha = 1.0 if cell in anciens_verdicts else t
                        c.create_text(x + cw / 2, y + ch * 0.82, text=texte,
                                      fill=blend(base, "#14532d" if optimal else "#991b1b", alpha),
                                      font=self.fit(texte, fs * 0.72, cw - 8, "bold"))

        # ---------------- rapport, nouveaux jeux ----------------
        def show_report(self):
            win = tk.Toplevel(self)
            win.title("Rapport complet : " + self.gvar.get())
            win.configure(bg=BG)
            win.geometry("920x640")
            rapport = rapport_complet(self.jeu)
            bar = tk.Frame(win, bg=BG)
            bar.pack(fill="x", padx=14, pady=10)

            def copier():
                self.clipboard_clear()
                self.clipboard_append(rapport)

            def enregistrer():
                chemin = filedialog.asksaveasfilename(parent=win, defaultextension=".txt",
                                                      filetypes=[("Texte", "*.txt")])
                if chemin:
                    with open(chemin, "w", encoding="utf-8") as f:
                        f.write(rapport + "\n")

            Btn(bar, "Copier", copier).pack(side="left", padx=(0, 6))
            Btn(bar, "Enregistrer…", enregistrer).pack(side="left")
            zone = tk.Frame(win, bg=BG)
            zone.pack(fill="both", expand=True, padx=14, pady=(0, 14))
            ys = tk.Scrollbar(zone, orient="vertical")
            xs = tk.Scrollbar(zone, orient="horizontal")
            box = tk.Text(zone, bg=CARD, fg=TXT, relief="flat", font=("Courier", 11), padx=12, pady=8,
                          wrap="none", highlightthickness=0, yscrollcommand=ys.set, xscrollcommand=xs.set)
            ys.configure(command=box.yview)
            xs.configure(command=box.xview)
            ys.pack(side="right", fill="y")
            xs.pack(side="bottom", fill="x")
            box.pack(side="left", fill="both", expand=True)
            box.insert("1.0", rapport)
            box.configure(state="disabled")

        def ajouter_perso(self, titre, jeu):
            self.perso.append((titre, jeu))
            self.charger(jeu, titre)

        def new_random(self):
            s = simpledialog.askstring("Jeu aléatoire", "Nombre de stratégies : m n\n(ex : 4 4)",
                                       initialvalue="4 4", parent=self)
            if not s:
                return
            try:
                m, n = (int(x) for x in s.split())
                if not (1 <= m <= 12 and 1 <= n <= 12):
                    raise ValueError
            except ValueError:
                messagebox.showerror("Erreur", "Entrez deux entiers entre 1 et 12 (ex : 4 4).", parent=self)
                return
            A = [[random.randint(-5, 10) for _ in range(n)] for _ in range(m)]
            B = [[random.randint(-5, 10) for _ in range(n)] for _ in range(m)]
            titre = f"Aléatoire {m}×{n}"
            self.ajouter_perso(titre, Jeu(A, B, titre))

        def new_matrix(self):
            win = tk.Toplevel(self)
            win.title("Saisir une matrice")
            win.configure(bg=BG)
            tk.Label(win, bg=BG, fg=MUTED, justify="left", padx=16, pady=10,
                     text="Une ligne = une stratégie du joueur 1.\n"
                          "Chaque case = « u1,u2 », séparées par des espaces.\n"
                          "Lignes facultatives « J1: … » et « J2: … » pour nommer les stratégies.\n"
                          "Exemple :\nJ1: H B\nJ2: G D\n0,0 2,2\n10,11 -1,0").pack(anchor="w")
            box = tk.Text(win, width=48, height=9, bg=CARD, fg=TXT, insertbackground=TXT,
                          relief="flat", font=("Courier", 12), padx=10, pady=8)
            box.insert("1.0", "J1: H B\nJ2: G D\n0,0 2,2\n10,11 -1,0")
            box.pack(padx=16)

            def ok():
                try:
                    jeu = jeu_depuis_texte(box.get("1.0", "end"))
                except ValueError as erreur:
                    messagebox.showerror("Erreur", str(erreur) or "Format invalide.", parent=win)
                    return
                win.destroy()
                titre = f"Jeu saisi {jeu.m}×{jeu.n}"
                jeu.nom = titre
                self.ajouter_perso(titre, jeu)

            Btn(win, "Valider", ok, ACCENT).pack(pady=12)

        def new_file(self):
            chemin = filedialog.askopenfilename(parent=self, filetypes=[("Jeux texte", "*.txt"),
                                                                         ("Tous les fichiers", "*.*")])
            if chemin:
                try:
                    jeu = lire_fichier(chemin)
                except (ValueError, OSError) as erreur:
                    messagebox.showerror("Erreur de chargement", str(erreur), parent=self)
                    return
                self.ajouter_perso(chemin.replace("\\", "/").split("/")[-1], jeu)

        def save_game(self):
            chemin = filedialog.asksaveasfilename(parent=self, defaultextension=".txt",
                                                  filetypes=[("Jeux texte", "*.txt")])
            if chemin:
                try:
                    ecrire_fichier(self.jeu, chemin)
                except OSError as erreur:
                    messagebox.showerror("Erreur", str(erreur), parent=self)


def lancer_gui() -> bool:
    """Ouvre l'interface graphique. Renvoie False (avec un message) si c'est impossible."""
    if not HAS_TK:
        print("Tkinter est absent : interface graphique indisponible. "
              "(Linux : sudo apt install python3-tk)", file=sys.stderr)
        return False
    try:
        app = App()
    except tk.TclError as erreur:
        print(f"Affichage graphique indisponible ({erreur}).", file=sys.stderr)
        return False
    app.mainloop()
    return True


# =============================================================================
# 10. Interface en ligne de commande
# =============================================================================

def _configurer_sortie() -> None:
    """Force l'UTF-8 pour les accents (utile sous Windows)."""
    for flux in (sys.stdout, sys.stderr):
        try:
            flux.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass


def _afficher_liste_exemples() -> None:
    print("Exemples disponibles (--exemple NOM) :")
    for cle, ex in EXEMPLES.items():
        print(f"  {cle:<24} [{ex.source}]\n  {'':<24} {ex.description}")


def _proposer_sauvegarde(jeu: Jeu) -> None:
    chemin = input("\nSauvegarder ce jeu dans un fichier ? (chemin, ou Entrée pour ignorer) : ").strip()
    if chemin:
        ecrire_fichier(jeu, chemin)
        print(f"Jeu sauvegardé dans '{chemin}'.")


def _menu(complements: bool) -> None:
    while True:
        print("\n=== TP 2 - Équilibres de Nash en stratégies pures ===")
        print("  1) Saisir un jeu au clavier")
        print("  2) Charger un jeu depuis un fichier")
        print("  3) Choisir un exemple du cours")
        print("  4) Lancer tous les exemples")
        print("  0) Quitter")
        choix = input("Votre choix : ").strip()
        try:
            if choix == "1":
                jeu = saisir_jeu_clavier()
                print(rapport_complet(jeu, complements))
                _proposer_sauvegarde(jeu)
            elif choix == "2":
                print(rapport_complet(lire_fichier(input("Chemin du fichier : ").strip()),
                                      complements))
            elif choix == "3":
                _afficher_liste_exemples()
                cle = input("Nom de l'exemple : ").strip()
                if cle in EXEMPLES:
                    print(rapport_complet(EXEMPLES[cle].jeu(), complements))
                else:
                    print("  -> Exemple inconnu.")
            elif choix == "4":
                for ex in EXEMPLES.values():
                    print(rapport_complet(ex.jeu(), complements))
                    print()
            elif choix == "0":
                return
            else:
                print("  -> Choix invalide.")
        except (ValueError, OSError) as erreur:
            print(f"  -> Erreur : {erreur}")


def main(argv: Sequence[str] | None = None) -> int:
    _configurer_sortie()
    parseur = argparse.ArgumentParser(
        description="TP 2 - Équilibres de Nash en stratégies pures (jeu à deux joueurs).")
    parseur.add_argument("-f", "--fichier", help="charger un jeu depuis un fichier texte")
    parseur.add_argument("-k", "--clavier", action="store_true", help="saisir un jeu au clavier")
    parseur.add_argument("-e", "--exemple", help="analyser un exemple du cours (voir --liste-exemples)")
    parseur.add_argument("--liste-exemples", action="store_true", help="lister les exemples du cours")
    parseur.add_argument("--tous-les-exemples", action="store_true", help="analyser tous les exemples")
    parseur.add_argument("--sans-complements", action="store_true",
                         help="n'afficher que les résultats demandés par le TP (R2 à R6)")
    parseur.add_argument("--gui", action="store_true", help="ouvrir l'interface graphique")
    parseur.add_argument("--console", action="store_true",
                         help="menu en mode console (sans interface graphique)")
    parseur.add_argument("--selftest", action="store_true",
                         help="vérifier en console tous les exemples du cours")
    args = parseur.parse_args(argv)
    complements = not args.sans_complements

    if args.selftest:
        return 0 if selftest() else 1

    try:
        if args.liste_exemples:
            _afficher_liste_exemples()
        elif args.tous_les_exemples:
            for ex in EXEMPLES.values():
                print(rapport_complet(ex.jeu(), complements))
                print()
        elif args.exemple:
            if args.exemple not in EXEMPLES:
                print(f"Exemple inconnu : '{args.exemple}'.", file=sys.stderr)
                _afficher_liste_exemples()
                return 2
            print(rapport_complet(EXEMPLES[args.exemple].jeu(), complements))
        elif args.fichier:
            print(rapport_complet(lire_fichier(args.fichier), complements))
        elif args.clavier:
            jeu = saisir_jeu_clavier()
            print(rapport_complet(jeu, complements))
            _proposer_sauvegarde(jeu)
        elif args.console:
            _menu(complements)
        elif not lancer_gui():
            if args.gui:
                return 1
            print("-> menu console à la place.\n", file=sys.stderr)
            _menu(complements)
    except (ValueError, OSError) as erreur:
        print(f"Erreur : {erreur}", file=sys.stderr)
        return 1
    except (EOFError, KeyboardInterrupt):
        print("\nInterrompu.")
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main())
