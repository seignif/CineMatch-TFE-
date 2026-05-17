import { Link } from 'react-router-dom'

export default function CGU() {
  return (
    <div className="min-h-screen px-4 py-12 max-w-3xl mx-auto">
      <div className="mb-8">
        <Link to="/films" className="font-display text-2xl tracking-wider">
          CINE<span style={{ color: 'var(--accent-red)' }}>MATCH</span>
        </Link>
      </div>

      <div className="glass rounded-2xl p-8 space-y-8">
        <div>
          <h1 className="font-display text-3xl tracking-wider text-white mb-2">
            CONDITIONS GÉNÉRALES D'UTILISATION
          </h1>
          <p className="text-[var(--text-muted)] text-sm">Dernière mise à jour : Mai 2026</p>
        </div>

        <section>
          <h2 className="text-lg font-semibold text-white mb-3">1. Objet</h2>
          <p className="text-[var(--text-muted)] leading-relaxed">
            CineMatch est une plateforme web de mise en relation de cinéphiles belges, permettant de
            découvrir des films en salle, de matcher avec d'autres passionnés et d'organiser des sorties
            au cinéma. Les présentes Conditions Générales d'Utilisation (CGU) régissent l'accès et
            l'utilisation du service CineMatch.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-semibold text-white mb-3">2. Accès au service</h2>
          <p className="text-[var(--text-muted)] leading-relaxed mb-2">
            L'utilisation de CineMatch est réservée aux personnes physiques âgées de 16 ans ou plus.
            L'inscription implique la création d'un compte avec une adresse email valide et un mot de passe.
          </p>
          <p className="text-[var(--text-muted)] leading-relaxed">
            L'utilisateur est responsable de la confidentialité de ses identifiants et de toute activité
            effectuée depuis son compte.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-semibold text-white mb-3">3. Règles de la communauté</h2>
          <p className="text-[var(--text-muted)] leading-relaxed mb-3">
            CineMatch est une communauté bienveillante. Les contenus suivants sont strictement interdits :
          </p>
          <ul className="space-y-2 mb-4">
            {[
              "Harcèlement, intimidation ou menaces envers d'autres utilisateurs",
              "Contenus racistes, discriminatoires, haineux ou xénophobes",
              "Contenus sexuels non sollicités ou explicites",
              "Spam, publicités non autorisées ou messages répétitifs",
              "Usurpation d'identité ou fausses informations",
              "Contenus portant atteinte à des droits de tiers (droits d'auteur, vie privée)",
            ].map(rule => (
              <li key={rule} className="flex items-start gap-2 text-[var(--text-muted)] text-sm">
                <span style={{ color: 'var(--accent-red)' }} className="mt-0.5 shrink-0">•</span>
                {rule}
              </li>
            ))}
          </ul>
          <p className="text-[var(--text-muted)] leading-relaxed text-sm">
            En cas de violation, CineMatch se réserve le droit de supprimer le contenu, d'émettre un
            avertissement, de suspendre temporairement ou de supprimer définitivement le compte concerné,
            sans préavis ni remboursement.
          </p>
        </section>

        <section id="confidentialite">
          <h2 className="text-lg font-semibold text-white mb-3">4. Données personnelles (RGPD)</h2>
          <p className="text-[var(--text-muted)] leading-relaxed mb-2">
            Conformément au Règlement Général sur la Protection des Données (RGPD), vous disposez des
            droits suivants sur vos données personnelles :
          </p>
          <ul className="space-y-2 mb-4">
            {[
              "Droit d'accès : téléchargez vos données depuis votre profil (onglet Paramètres)",
              "Droit à l'effacement : supprimez votre compte depuis votre profil (onglet Paramètres)",
              "Droit de rectification : modifiez vos informations depuis votre profil",
              "Droit à la portabilité : export JSON de toutes vos données",
            ].map(right => (
              <li key={right} className="flex items-start gap-2 text-[var(--text-muted)] text-sm">
                <span style={{ color: 'var(--accent-gold)' }} className="mt-0.5 shrink-0">•</span>
                {right}
              </li>
            ))}
          </ul>
          <p className="text-[var(--text-muted)] leading-relaxed text-sm">
            Les données collectées (email, prénom, ville, préférences) sont utilisées uniquement pour
            le fonctionnement du service. Elles ne sont pas vendues à des tiers. La base légale du
            traitement est le consentement (acceptation des CGU lors de l'inscription).
          </p>
        </section>

        <section>
          <h2 className="text-lg font-semibold text-white mb-3">5. Propriété intellectuelle</h2>
          <p className="text-[var(--text-muted)] leading-relaxed">
            Les données de films proviennent de Kinepolis et de TMDb. CineMatch n'est pas affilié à
            ces entités. Les affiches et informations de films restent la propriété de leurs ayants droit
            respectifs. Le code source et le design de CineMatch sont la propriété de l'auteur.
          </p>
        </section>

        <section>
          <h2 className="text-lg font-semibold text-white mb-3">6. Contact</h2>
          <p className="text-[var(--text-muted)] leading-relaxed">
            Pour toute question relative à ces CGU ou à vos données personnelles :{' '}
            <a href="mailto:contact@cinematch.be"
              className="underline hover:text-white transition-colors"
              style={{ color: 'var(--accent-red)' }}>
              contact@cinematch.be
            </a>
          </p>
        </section>

        <div className="pt-4 border-t border-white/10 text-center">
          <Link to="/films" className="text-sm hover:text-white transition-colors"
            style={{ color: 'var(--accent-red)' }}>
            Retour à CineMatch
          </Link>
        </div>
      </div>
    </div>
  )
}
