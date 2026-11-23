# THE LEGENDS — Prototype v0.1

Une première application installable **PWA**, au style noir et or, conçue pour Android et iPhone.

## Démonstration immédiate

1. Ouvrir `index.html` dans un navigateur sur ordinateur pour tester les fonctions locales (ou héberger le dossier en HTTPS pour installer sur téléphone).
2. Essayer le calendrier, le menu, l'ajout et la modification de soirées, les réponses de participation, les checklists, les budgets et les commentaires.
3. Le mode démonstration sauvegarde les données dans le navigateur via `localStorage`. Ce mode ne synchronise PAS les téléphones et n'offre pas d'authentification réelle.

Pour un test local avec HTTP :

```bash
python3 -m http.server 8080
```

Puis ouvrir `http://localhost:8080` sur le même ordinateur. L'installation PWA nécessite normalement HTTPS, sauf localhost.

## Installation privée sur téléphone

Publier les fichiers statiques sur **Cloudflare Pages** (ou tout hébergement HTTPS).

1. Créer un site Pages et déposer le contenu du dossier `the-legends` comme site statique.
2. Ouvrir le lien HTTPS reçu sur Android : menu du navigateur → **Installer l'application** ou **Ajouter à l'écran d'accueil**.
3. Sur iPhone : ouvrir dans Safari → Partager → **Sur l'écran d'accueil**.

Le lien de la version démonstration n'est PAS un système d'invitation sécurisé. Pour restreindre l'accès aux vraies données, configurer Supabase et les règles RLS fournies.

## Activer Supabase (mode multi-utilisateurs expérimental)

**Important : étape réservée aux tests techniques.** Le mode connecté est un socle, pas encore une version de production complète. En particulier, le traitement des suppressions de compte, la confidentialité des photos et les imports/restaurations serveur restent à développer.

1. Créer un projet Supabase.
2. Dans **SQL Editor**, exécuter le fichier `supabase/schema.sql`.
3. Dans **Authentication → Providers**, activer Email et, si souhaité, Google. Configurer correctement l'URL du site et les URL de redirection.
4. Configurer `config.js` :

```js
window.LEGENDS_CONFIG = {
  supabaseUrl: 'https://VOTRE-PROJET.supabase.co',
  supabaseAnonKey: 'VOTRE_CLE_PUBLIQUE_ANON_OU_PUBLISHABLE'
};
```

**Ne JAMAIS mettre de clé `service_role` ni de clé secrète dans ce fichier.**

5. Ouvrir l'application et créer le premier compte administrateur. Ce compte sera en attente jusqu'à promotion manuelle depuis SQL Editor :

```sql
-- Remplacer l'adresse par celle du compte administrateur initial.
update public.profiles
set role = 'admin'
where id = (select id from auth.users where email = 'VOTRE_EMAIL@example.com');
```

6. Reconnecter le premier compte, puis créer celui de Pauline et lui attribuer le rôle administrateur avec une requête similaire dans SQL Editor. Les autres utilisateurs passent par une demande d'inscription et apparaissent en attente, à approuver dans la rubrique Amis.
7. Tester en ouvrant deux navigateurs distincts et en vérifiant la synchronisation des soirées.

### Points à ne pas confondre avec des fonctionnalités terminées

- Recherche quotidienne de soirées et récupération externe : **pas encore implémentées**.
- Notifications push : **pas encore implémentées**.
- Photos collaboratives privées : **pas encore implémentées** dans le mode Supabase ; photo locale de test seulement en démo.
- Gestion réelle des invitations par jeton : **pas encore implémentée**. Le mode connecté utilise l'inscription suivie d'approbation.
- Sauvegarde complète et restauration serveur : **pas encore implémentées**. Export/import JSON = démo locale seulement.
- Délai de suppression de compte 7 jours : **pas encore implémenté**.
- La confirmation du couple est fondée sur les votes des **deux comptes administrateurs**.
- Fonctionnalités complémentaires (billets détaillés, gardienne, hôtel, notes personnelles avec confidentialité, réactions, détection des doublons) : **à développer**.

## Architecture

- `index.html` : entrée de l'application.
- `styles.css` : styles noir/or, calendrier, menu et fiches.
- `app.js` : interface et logique, navigateur pur (sans compilation).
- `manifest.webmanifest`, `icon.svg`, `sw.js` : installation progressive et cache.
- `config.js` : configuration publique (vierge par défaut).
- `supabase/schema.sql` : tables, fonctions et contrôles d'accès RLS.

## Limites et sécurité

Cette version est destinée à la validation du premier prototype. Vérifier les politiques RLS avec plusieurs comptes et effectuer un audit avant de mettre des données sensibles réelles dans l'application. Les données du mode démonstration sont accessibles à toute personne disposant du même navigateur/profil. Ne pas y stocker de photos ou notes sensibles. Les exportations JSON ne sont pas chiffrées.
