#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests de validation du TP 2 (R7), fondés sur les exemples et résultats des slides du cours.

Lancer :   python test_nash.py          (ou : python -m unittest -v)
Aucune dépendance externe : seulement la bibliothèque standard.

Convention : les profils sont des indices à partir de 0, (0, 0) = (A1, B1) = première
ligne, première colonne.
"""

import os
import random
import tempfile
import time
import unittest

import nash_equilibrium as ne
from nash_equilibrium import (
    EXEMPLES, Jeu, analyser, calculer_securite, domine, dominants, ecrire_fichier,
    est_equilibre_nash, extraire_nombres, interchangeables, jeu_depuis_couples,
    jeu_depuis_nombres, lire_fichier, meilleures_reponses_j1, meilleures_reponses_j2,
    profils_pareto_optimaux, rapport_complet,
    construire_etapes, groupe_exemple, jeu_depuis_texte, selftest,
)

DOSSIER = os.path.dirname(os.path.abspath(__file__))


def idx(jeu, nom1, nom2):
    """Profil (i, j) à partir des noms de stratégies, pour écrire les tests comme les slides."""
    return jeu.noms_j1.index(nom1), jeu.noms_j2.index(nom2)


class TestExerciceCours(unittest.TestCase):
    """Chap. 3, exercice 2 = exemple du sujet : BR1, BR2 et NE recopiés des slides."""

    def setUp(self):
        self.jeu = EXEMPLES["sujet"].jeu()
        self.analyse = analyser(self.jeu)

    def test_meilleures_reponses_joueur_1(self):
        # BR1 = {(A1,B1),(A1,B2),(A1,B3),(A2,B4)}
        self.assertEqual(self.analyse.ensemble_br1, {(0, 0), (0, 1), (0, 2), (1, 3)})

    def test_meilleures_reponses_joueur_2(self):
        # BR2 = {(A1,B1),(A2,B3),(A2,B4),(A3,B1),(A3,B3),(A4,B2),(A4,B4)}
        self.assertEqual(self.analyse.ensemble_br2,
                         {(0, 0), (1, 2), (1, 3), (2, 0), (2, 2), (3, 1), (3, 3)})

    def test_equilibres_de_nash_et_gains(self):
        self.assertEqual(self.analyse.equilibres, [(0, 0), (1, 3)])
        self.assertEqual(self.jeu.gains((0, 0)), (26, 10))
        self.assertEqual(self.jeu.gains((1, 3)), (22, 8))

    def test_pareto(self):
        # Le slide : (A1,B1) est le Pareto dominant ; l'autre équilibre est dominé.
        self.assertTrue(domine(self.jeu, (0, 0), (1, 3)))
        self.assertEqual(self.analyse.equilibres_pareto_optimaux, [(0, 0)])
        self.assertEqual(self.analyse.equilibres_domines, [(1, 3)])

    def test_plusieurs_meilleures_reponses_pour_un_joueur(self):
        br2 = meilleures_reponses_j2(self.jeu)
        self.assertEqual(br2[1], [2, 3])   # R2(A2) = {B3, B4}
        self.assertEqual(br2[2], [0, 2])   # R2(A3) = {B1, B3}


class TestExemplesChapitre3(unittest.TestCase):

    def test_exemple_3_3_meilleures_reponses_des_slides(self):
        a = analyser(EXEMPLES["ex3_3"].jeu())
        # Joueur 1 : (A3,B1), (A1,B2), (A2,B3)
        self.assertEqual(a.ensemble_br1, {(2, 0), (0, 1), (1, 2)})
        # Joueur 2 : (A1,B1), (A2,B3), (A3,B3)
        self.assertEqual(a.ensemble_br2, {(0, 0), (1, 2), (2, 2)})
        self.assertEqual(a.equilibres, [(1, 2)])

    def test_exemple_3_1_deux_equilibres_dont_un_pareto_optimal(self):
        jeu = EXEMPLES["ex3_1"].jeu()
        a = analyser(jeu)
        self.assertEqual(sorted(a.equilibres), sorted([idx(jeu, "B", "G"), idx(jeu, "H", "D")]))
        # (B,G) = (10,11) est un équilibre et un optimum de Pareto ; il domine (H,D) = (2,2)
        self.assertEqual(a.equilibres_pareto_optimaux, [idx(jeu, "B", "G")])

    def test_exemple_3_2_unique_equilibre_B_R(self):
        jeu = EXEMPLES["ex3_2"].jeu()
        self.assertEqual(analyser(jeu).equilibres, [idx(jeu, "B", "R")])
        self.assertEqual(jeu.gains(idx(jeu, "B", "R")), (5, 5))

    def test_exemple_3_4_la_dominance_faible_ecarte_un_equilibre(self):
        # Le cours : l'élimination faible donne (H,D) mais écarte l'équilibre (B,G).
        jeu = EXEMPLES["ex3_4"].jeu()
        a = analyser(jeu)
        self.assertIn(idx(jeu, "B", "G"), a.equilibres)
        self.assertIn(idx(jeu, "H", "D"), a.equilibres)
        self.assertEqual(a.br1[0], [0, 1])   # R1(G) = {H, B} : ex æquo

    def test_carrefour_equilibres_P_S_et_S_P(self):
        jeu = EXEMPLES["carrefour"].jeu()
        self.assertEqual(sorted(analyser(jeu).equilibres),
                         sorted([idx(jeu, "P", "S"), idx(jeu, "S", "P")]))

    def test_bataille_du_couple(self):
        jeu = EXEMPLES["bataille_couple"].jeu()
        self.assertEqual(analyser(jeu).equilibres,
                         [idx(jeu, "Théâtre", "Théâtre"), idx(jeu, "Foot", "Foot")])

    def test_pierre_feuille_ciseaux_et_tir_au_but_sans_equilibre_pur(self):
        for cle in ("pierre_feuille_ciseaux", "tir_au_but"):
            with self.subTest(jeu=cle):
                self.assertEqual(analyser(EXEMPLES[cle].jeu()).equilibres, [])
        rapport = rapport_complet(EXEMPLES["tir_au_but"].jeu())
        self.assertIn("Aucun équilibre de Nash en stratégies pures", rapport)

    def test_dell_compaq_exercice_1(self):
        jeu = EXEMPLES["dell_compaq"].jeu()
        a = analyser(jeu)
        W, L = 0, 1
        # BR1 = {(W,A),(W,B),(W,C),(L,C),(L,D)} ; BR2 = {(W,A),(W,B),(L,A),(L,D)}
        self.assertEqual(a.ensemble_br1, {(W, 0), (W, 1), (W, 2), (L, 2), (L, 3)})
        self.assertEqual(a.ensemble_br2, {(W, 0), (W, 1), (L, 0), (L, 3)})
        self.assertEqual(a.equilibres, [(W, 0), (W, 1), (L, 3)])

    def test_choix_d_un_chiffre_seul_10_10_est_pareto_optimal(self):
        jeu = EXEMPLES["chiffre"].jeu()
        a = analyser(jeu)
        self.assertEqual(a.equilibres, [(k, k) for k in range(10)])        # 10 NE (a, a)
        self.assertEqual(a.equilibres_pareto_optimaux, [(9, 9)])           # seul (10,10)
        self.assertEqual(jeu.gains((9, 9)), (100, 100))


class TestExemplesChapitre2(unittest.TestCase):

    def test_dilemme_seul_profil_non_pareto_optimal_est_l_equilibre(self):
        # Remarque du cours : dans le dilemme, le seul profil dominé est l'équilibre de Nash.
        jeu = EXEMPLES["dilemme"].jeu()
        a = analyser(jeu)
        self.assertEqual(a.equilibres, [(0, 0)])
        non_optimaux = [p for p in jeu.profils() if p not in profils_pareto_optimaux(jeu)]
        self.assertEqual(non_optimaux, [(0, 0)])
        self.assertTrue(domine(jeu, (1, 1), (0, 0)))   # (N'avoue pas, N'avoue pas) domine

    def test_essd_donne_l_unique_equilibre_proposition_3_1(self):
        # Chap. 2 : l'ESSD conduit à (H,G) ; la proposition 3.1 en fait l'unique NE.
        jeu = EXEMPLES["essd_chap2"].jeu()
        self.assertEqual(analyser(jeu).equilibres, [idx(jeu, "H", "G")])

    def test_dominance_faible_il_y_a_plus_d_equilibres_que_ceux_des_eliminations(self):
        # Le cours trouve (M,L) ou (M,R) selon l'ordre ; ils sont bien des NE, mais il y en a 4.
        jeu = EXEMPLES["dominance_faible_chap2"].jeu()
        a = analyser(jeu)
        self.assertIn(idx(jeu, "M", "L"), a.equilibres)
        self.assertIn(idx(jeu, "M", "R"), a.equilibres)
        self.assertEqual(len(a.equilibres), 4)
        # (M,L) = (2,2) est dominé par (T,C) = (2,3) : domination faible
        self.assertTrue(domine(jeu, idx(jeu, "T", "C"), idx(jeu, "M", "L")))


class TestSecuriteChapitres3Et4(unittest.TestCase):

    def test_maxmin_chap4_valeurs_des_slides(self):
        jeu = EXEMPLES["maxmin_chap4"].jeu()
        sec = calculer_securite(jeu)
        self.assertEqual((sec.maxmin_j1, sec.maxmin_j2), (2, 1))       # v1 = 2, v2 = 1
        self.assertEqual(sec.profils_prudents, [idx(jeu, "T", "L")])   # maxmin = (T,L)
        self.assertEqual(jeu.gains(idx(jeu, "T", "L")), (3, 1))        # 3 > v1 = 2
        # et l'équilibre de Nash est un autre profil : (B,R)
        self.assertEqual(analyser(jeu).equilibres, [idx(jeu, "B", "R")])

    def test_plusieurs_strategies_maxmin(self):
        # Le cours : le paiement maxmin peut valoir (2,3) ou (1,1).
        jeu = EXEMPLES["maxmin_multiple"].jeu()
        sec = calculer_securite(jeu)
        self.assertEqual(sec.profils_prudents, [idx(jeu, "B", "L"), idx(jeu, "B", "R")])
        self.assertEqual(sorted(jeu.gains(p) for p in sec.profils_prudents), [(1, 1), (2, 3)])

    def test_poule_mouillee_maxmin_n_est_pas_nash(self):
        jeu = EXEMPLES["poule_mouillee"].jeu()
        sec = calculer_securite(jeu)
        devier = idx(jeu, "Dévier", "Dévier")
        self.assertEqual(sec.profils_prudents, [devier])
        self.assertNotIn(devier, analyser(jeu).equilibres)

    def test_dilemme_maxmin_et_nash_coincident(self):
        # Corollaire 2 du cours : stratégies strictement dominantes => Nash = maxmin.
        jeu = EXEMPLES["dilemme"].jeu()
        self.assertEqual(calculer_securite(jeu).profils_prudents, analyser(jeu).equilibres)

    def test_pareto_versus_securite(self):
        # Chap. 3, exemple 2 : (U,U) est Pareto-optimal mais sa garantie est 0 ; (V,V) garantit 7.
        jeu = EXEMPLES["securite"].jeu()
        sec = calculer_securite(jeu)
        self.assertEqual(sec.garanties_j1, [0, 7])
        self.assertEqual((sec.maxmin_j1, sec.maxmin_j2), (7, 7))
        self.assertEqual(sec.profils_prudents, [idx(jeu, "V", "V")])

    def test_un_equilibre_garantit_au_moins_le_niveau_de_securite(self):
        # u_i(s*) >= max_si u_i(si, s*_-i) >= maxmin_i  : vrai pour tout NE de tout jeu.
        hasard = random.Random(11)
        for _ in range(300):
            m, n = hasard.randint(1, 5), hasard.randint(1, 5)
            A = [[hasard.randint(-3, 3) for _ in range(n)] for _ in range(m)]
            B = [[hasard.randint(-3, 3) for _ in range(n)] for _ in range(m)]
            jeu = Jeu(A, B)
            sec = calculer_securite(jeu)
            for e in analyser(jeu).equilibres:
                u1, u2 = jeu.gains(e)
                self.assertGreaterEqual(u1, sec.maxmin_j1)
                self.assertGreaterEqual(u2, sec.maxmin_j2)


class TestInterchangeabilite(unittest.TestCase):

    def test_dell_compaq(self):
        jeu = EXEMPLES["dell_compaq"].jeu()
        # (W,A) et (W,B) : les profils croisés sont (W,B) et (W,A), tous deux NE
        self.assertTrue(interchangeables(jeu, (0, 0), (0, 1)))
        # (W,A) et (L,D) : (W,D) n'est pas un NE
        self.assertFalse(interchangeables(jeu, (0, 0), (1, 3)))

    def test_carrefour_et_bataille_ne_sont_pas_interchangeables(self):
        for cle in ("carrefour", "bataille_couple"):
            with self.subTest(jeu=cle):
                a = analyser(EXEMPLES[cle].jeu())
                (paire, oui), = a.interchangeabilite.items()
                self.assertFalse(oui)

    def test_un_equilibre_est_interchangeable_avec_lui_meme(self):
        jeu = EXEMPLES["sujet"].jeu()
        self.assertTrue(interchangeables(jeu, (0, 0), (0, 0)))


class TestJeuxDEssai(unittest.TestCase):
    """Chaque exemple du cours : NE attendus et NE dominés attendus."""

    def test_tous_les_exemples(self):
        for cle, ex in EXEMPLES.items():
            with self.subTest(exemple=cle):
                a = analyser(ex.jeu())
                self.assertEqual(a.equilibres, sorted(ex.equilibres_attendus))
                self.assertEqual(a.equilibres_domines, sorted(ex.domines_attendus))

    def test_les_categories_exigees_par_le_sujet_sont_couvertes(self):
        nb_ne = {cle: len(analyser(ex.jeu()).equilibres) for cle, ex in EXEMPLES.items()}
        self.assertTrue(any(k == 1 for k in nb_ne.values()), "un seul NE")
        self.assertTrue(any(k >= 2 for k in nb_ne.values()), "plusieurs NE")
        self.assertTrue(any(k == 0 for k in nb_ne.values()), "aucun NE")
        self.assertTrue(any(                                   # meilleures réponses multiples
            any(len(r) > 1 for r in meilleures_reponses_j1(ex.jeu()).values())
            or any(len(r) > 1 for r in meilleures_reponses_j2(ex.jeu()).values())
            for ex in EXEMPLES.values()))
        self.assertTrue(any(analyser(ex.jeu()).equilibres_domines for ex in EXEMPLES.values()))
        self.assertTrue(any(analyser(ex.jeu()).equilibres_pareto_optimaux
                            for ex in EXEMPLES.values()))
        # un jeu non carré (m != n) et un jeu 'grand' (10 x 10)
        formes = {(ex.jeu().m, ex.jeu().n) for ex in EXEMPLES.values()}
        self.assertTrue(any(m != n for m, n in formes))
        self.assertIn((10, 10), formes)

    def test_domination_faible(self):
        # (T,C) = (2,3) domine (M,L) = (2,2) : une seule inégalité stricte suffit
        jeu = EXEMPLES["dominance_faible_chap2"].jeu()
        self.assertTrue(domine(jeu, idx(jeu, "T", "C"), idx(jeu, "M", "L")))
        self.assertFalse(domine(jeu, idx(jeu, "M", "L"), idx(jeu, "T", "C")))

    def test_un_profil_ne_se_domine_pas_lui_meme(self):
        jeu = EXEMPLES["sujet"].jeu()
        for p in jeu.profils():
            self.assertFalse(domine(jeu, p, p))
            self.assertNotIn(p, dominants(jeu, p))

    def test_pareto_exige_une_inegalite_stricte(self):
        # gains identiques => pas de domination (ex. (A2,B3) et (A2,B4) valent (22,8))
        jeu = EXEMPLES["sujet"].jeu()
        self.assertFalse(domine(jeu, (1, 2), (1, 3)))
        self.assertFalse(domine(jeu, (1, 3), (1, 2)))


class TestVerificationCroisee(unittest.TestCase):
    """BR1 inter BR2  doit coïncider avec le test direct de la définition 3.1 du cours."""

    def test_jeux_aleatoires(self):
        hasard = random.Random(2026)
        for _ in range(500):
            m, n = hasard.randint(1, 5), hasard.randint(1, 5)
            # gains dans {0,1,2} : beaucoup d'ex æquo, donc beaucoup de cas limites
            A = [[hasard.randint(0, 2) for _ in range(n)] for _ in range(m)]
            B = [[hasard.randint(0, 2) for _ in range(n)] for _ in range(m)]
            jeu = Jeu(A, B)
            par_br = analyser(jeu).equilibres
            par_definition = [p for p in jeu.profils() if est_equilibre_nash(jeu, p)]
            self.assertEqual(par_br, par_definition, msg=f"A={A} B={B}")

    def test_pareto_force_brute(self):
        hasard = random.Random(7)
        for _ in range(200):
            m, n = hasard.randint(1, 4), hasard.randint(1, 4)
            A = [[hasard.randint(0, 3) for _ in range(n)] for _ in range(m)]
            B = [[hasard.randint(0, 3) for _ in range(n)] for _ in range(m)]
            jeu = Jeu(A, B)
            # Définition du cours : s* est optimal s'il n'existe pas de profil t avec
            # u_i(t) >= u_i(s*) pour tout i et une inégalité stricte pour un joueur.
            attendu = [
                p for p in jeu.profils()
                if not any(
                    q != p
                    and jeu.gains(q)[0] >= jeu.gains(p)[0]
                    and jeu.gains(q)[1] >= jeu.gains(p)[1]
                    and jeu.gains(q) != jeu.gains(p)
                    for q in jeu.profils())
            ]
            self.assertEqual(profils_pareto_optimaux(jeu), attendu)

    def test_au_moins_un_profil_pareto_optimal(self):
        hasard = random.Random(3)
        for _ in range(100):
            m, n = hasard.randint(1, 4), hasard.randint(1, 4)
            A = [[hasard.randint(0, 3) for _ in range(n)] for _ in range(m)]
            B = [[hasard.randint(0, 3) for _ in range(n)] for _ in range(m)]
            self.assertTrue(profils_pareto_optimaux(Jeu(A, B)))

    def test_tolerance_flottante(self):
        # 0.1 + 0.2 et 0.3 sont "égaux" : les deux lignes sont des meilleures réponses
        jeu = Jeu([[0.1 + 0.2], [0.3]], [[1], [1]])
        self.assertEqual(meilleures_reponses_j1(jeu)[0], [0, 1])


class TestSaisieEtFichiers(unittest.TestCase):

    def test_extraction_des_nombres(self):
        self.assertEqual(extraire_nombres("(26, 10) (10, -2)"), [26, 10, 10, -2])
        self.assertEqual(extraire_nombres("1.5 0  4 1.25"), [1.5, 0, 4, 1.25])

    def test_lecture_du_fichier_du_sujet(self):
        jeu = lire_fichier(os.path.join(DOSSIER, "exemples", "cours.txt"))
        attendu = EXEMPLES["sujet"].jeu()
        self.assertEqual((jeu.A, jeu.B), (attendu.A, attendu.B))
        self.assertEqual(jeu.noms_j1, ["A1", "A2", "A3", "A4"])

    def test_lecture_avec_noms_de_strategies(self):
        jeu = lire_fichier(os.path.join(DOSSIER, "exemples", "dilemme.txt"))
        self.assertEqual(jeu.noms_j1, ["Avoue", "N'avoue pas"])
        attendu = EXEMPLES["dilemme"].jeu()
        self.assertEqual((jeu.A, jeu.B), (attendu.A, attendu.B))

    def test_tous_les_fichiers_d_exemples_sont_lisibles(self):
        dossier = os.path.join(DOSSIER, "exemples")
        for nom in sorted(os.listdir(dossier)):
            if nom.endswith(".txt"):
                with self.subTest(fichier=nom):
                    analyser(lire_fichier(os.path.join(dossier, nom)))

    def test_ecriture_puis_lecture(self):
        for cle in ("sujet", "bataille_couple", "dilemme", "maxmin_chap4"):
            with self.subTest(jeu=cle):
                jeu = EXEMPLES[cle].jeu()
                with tempfile.TemporaryDirectory() as tmp:
                    chemin = os.path.join(tmp, "jeu.txt")
                    ecrire_fichier(jeu, chemin)
                    relu = lire_fichier(chemin)
                self.assertEqual((relu.A, relu.B), (jeu.A, jeu.B))
                self.assertEqual((relu.noms_j1, relu.noms_j2), (jeu.noms_j1, jeu.noms_j2))

    def test_erreurs_de_saisie(self):
        with self.assertRaises(ValueError):
            jeu_depuis_nombres(2, 2, [1, 2, 3])                 # nombre de gains incorrect
        with self.assertRaises(ValueError):
            Jeu([[1, 2], [3]], [[1, 2], [3, 4]])                # matrice non rectangulaire
        with self.assertRaises(ValueError):
            Jeu([[1, 2]], [[1], [2]])                           # A et B de tailles différentes
        with self.assertRaises(ValueError):
            Jeu([], [])                                         # jeu vide
        with self.assertRaises(ValueError):
            Jeu([[float("nan")]], [[1]])                        # valeur non finie
        with self.assertRaises(ValueError):
            Jeu([[1, 2]], [[1, 2]], noms_j2=["G"])              # mauvais nombre de noms
        with self.assertRaises(ValueError):
            Jeu([[1, 2]], [[1, 2]], noms_j2=["G", "G"])         # noms en double

    def test_fichier_mal_forme(self):
        with tempfile.TemporaryDirectory() as tmp:
            chemin = os.path.join(tmp, "mauvais.txt")
            with open(chemin, "w", encoding="utf-8") as f:
                f.write("deux deux\n(1,1)\n")
            with self.assertRaises(ValueError):
                lire_fichier(chemin)

    def test_jeu_1x1(self):
        a = analyser(jeu_depuis_couples([[(5, 7)]]))
        self.assertEqual(a.equilibres, [(0, 0)])
        self.assertEqual(a.equilibres_pareto_optimaux, [(0, 0)])


class TestSaisieTexte(unittest.TestCase):
    """Zone de saisie de la matrice dans l'interface graphique."""

    def test_matrice_avec_noms(self):
        jeu = jeu_depuis_texte("J1: H B\nJ2: G D\n0,0 2,2\n10,11 -1,0")
        attendu = EXEMPLES["ex3_1"].jeu()
        self.assertEqual((jeu.A, jeu.B), (attendu.A, attendu.B))
        self.assertEqual((jeu.noms_j1, jeu.noms_j2), (["H", "B"], ["G", "D"]))

    def test_matrice_sans_noms_et_avec_commentaires(self):
        jeu = jeu_depuis_texte("# mon jeu\n(3,1) (2,3)  # ligne 1\n(1,2) (1,2)\n")
        self.assertEqual((jeu.m, jeu.n), (2, 2))
        self.assertEqual(jeu.noms_j1, ["A1", "A2"])

    def test_erreurs(self):
        for texte in ("", "J1: H B", "1,2 3,4\n1,2", "1,2,3", "a b c"):
            with self.subTest(texte=texte):
                with self.assertRaises(ValueError):
                    jeu_depuis_texte(texte)


class TestEtapesDeLInterface(unittest.TestCase):
    """Les étapes animées par le GUI (testables sans écran)."""

    def test_structure_des_etapes_pour_chaque_exemple(self):
        for cle, ex in EXEMPLES.items():
            with self.subTest(exemple=cle):
                jeu = ex.jeu()
                a = analyser(jeu)
                etapes = construire_etapes(a)
                k = len(a.equilibres)
                # départ + n colonnes + m lignes + intersection + k Pareto (+ bilan si k > 0)
                attendu = 1 + jeu.n + jeu.m + 1 + k + (1 if k else 0)
                self.assertEqual(len(etapes), attendu)
                self.assertEqual((etapes[0].br1, etapes[0].br2, etapes[0].ne),
                                 (frozenset(), frozenset(), frozenset()))
                derniere = etapes[-1]
                self.assertEqual(derniere.br1, frozenset(a.ensemble_br1))
                self.assertEqual(derniere.br2, frozenset(a.ensemble_br2))
                self.assertEqual(sorted(derniere.ne), a.equilibres)

    def test_les_marques_ne_font_que_s_ajouter(self):
        etapes = construire_etapes(analyser(EXEMPLES["sujet"].jeu()))
        for avant, apres in zip(etapes, etapes[1:]):
            self.assertLessEqual(avant.br1, apres.br1)
            self.assertLessEqual(avant.br2, apres.br2)
            self.assertLessEqual(avant.ne, apres.ne)
            self.assertLessEqual(len(avant.verdicts), len(apres.verdicts))

    def test_verdicts_de_pareto(self):
        a = analyser(EXEMPLES["sujet"].jeu())
        etapes = construire_etapes(a)
        self.assertEqual(dict(etapes[-1].verdicts), {(0, 0): True, (1, 3): False})
        # l'étape Pareto de (A2,B4) pointe ses dominants
        etape_ne2 = next(e for e in etapes if e.pareto == (1, 3))
        self.assertEqual(set(etape_ne2.dominants), {(0, 0), (0, 2), (2, 0), (2, 2)})

    def test_aucun_equilibre_pas_d_etape_pareto(self):
        etapes = construire_etapes(analyser(EXEMPLES["tir_au_but"].jeu()))
        self.assertIn("aucun équilibre", etapes[-1].texte)
        self.assertTrue(all(e.pareto is None for e in etapes))

    def test_rubriques_du_menu(self):
        groupes = {groupe_exemple(ex) for ex in EXEMPLES.values()}
        self.assertEqual(groupes, {"TP 2 (sujet)", "Chapitre 2", "Chapitre 3", "Chapitre 4"})

    def test_selftest_console(self):
        self.assertTrue(selftest())


@unittest.skipUnless(ne.HAS_TK, "Tkinter absent")
class TestInterfaceGraphique(unittest.TestCase):
    """Fumée de l'interface : nécessite un écran (sous Linux : xvfb-run -a python test_nash.py)."""

    @classmethod
    def setUpClass(cls):
        try:
            cls.app = ne.App()
        except Exception as erreur:          # pas d'affichage disponible
            raise unittest.SkipTest(f"affichage graphique indisponible : {erreur}")
        cls.app.update()

    @classmethod
    def tearDownClass(cls):
        cls.app.destroy()

    def attendre(self, condition, delai=10.0):
        fin = time.time() + delai
        while not condition() and time.time() < fin:
            self.app.update()
            time.sleep(0.01)
        self.assertTrue(condition(), "délai dépassé")

    def test_tous_les_exemples_se_dessinent_jusqu_au_bout(self):
        for cle in EXEMPLES:
            with self.subTest(exemple=cle):
                self.app.charger_exemple(cle)
                self.app.update()
                self.assertEqual(self.app.idx, 0)
                self.app.fin()
                self.app.update()
                self.assertEqual(self.app.idx, len(self.app.etapes) - 1)
                self.assertGreater(len(self.app.canvas.find_all()), 0)

    def test_pas_a_pas_retour_et_reinitialisation(self):
        self.app.charger_exemple("dilemme")
        self.app.speed.set(5)
        self.app.step()
        self.attendre(lambda: not self.app.busy)
        self.assertEqual(self.app.idx, 1)
        self.app.undo()
        self.assertEqual(self.app.idx, 0)
        self.app.aller_a(3)
        self.app.reset()
        self.assertEqual(self.app.idx, 0)

    def test_lecture_automatique_jusqu_a_la_fin(self):
        self.app.charger_exemple("dilemme")
        self.app.speed.set(5)
        self.app.on_play()
        self.attendre(lambda: not self.playing_ou_occupe())
        self.assertEqual(self.app.idx, len(self.app.etapes) - 1)

    def playing_ou_occupe(self):
        return self.app.playing or self.app.busy

    def test_reinitialiser_pendant_une_animation(self):
        self.app.charger_exemple("sujet")
        self.app.speed.set(1)
        self.app.step()
        self.app.update()
        self.app.reset()                      # annule l'animation en cours
        for _ in range(60):
            self.app.update()
            time.sleep(0.01)
        self.assertEqual(self.app.idx, 0)
        self.assertFalse(self.app.busy)

    def test_jeu_utilisateur_et_rapport(self):
        jeu = jeu_depuis_texte("J1: H B\nJ2: G D\n0,0 2,2\n10,11 -1,0", "Jeu saisi 2×2")
        self.app.ajouter_perso("Jeu saisi 2×2", jeu)
        self.assertEqual(len(self.app.perso), 1)
        self.app.fin()
        self.assertEqual(self.app.analyse.equilibres, [(0, 1), (1, 0)])
        self.app.show_report()
        self.app.update()


if __name__ == "__main__":
    unittest.main(verbosity=2)
