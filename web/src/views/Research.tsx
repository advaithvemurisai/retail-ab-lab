import { Header } from '../components/ui'

const link = (href: string, text: string) => <a href={href} target="_blank" rel="noreferrer">{text}</a>

export default function Research() {
  return (
    <div className="prose">
      <Header eyebrow="Evidence" title="Research" />
      <h3>Methods</h3>
      <ul>
        <li>{link('https://exp-platform.com/Documents/2013-02-CUPED-ImprovingSensitivityOfControlledExperiments.pdf', 'CUPED')} (Deng, Xu, Kohavi, Walker 2013): pre-period covariates reduce variance by ρ².</li>
        <li>{link('https://exp-platform.com/Documents/2019_KDDFabijanGupchupFuptaOmhoverVermeerDmitriev.pdf', 'SRM taxonomy')} (Fabijan et al. 2019): allocation failures should stop interpretation.</li>
        <li>{link('https://arxiv.org/abs/1512.04922', 'Always-valid inference')} (Johari, Pekelis, Walsh 2015): repeated looks need sequential correction.</li>
        <li>{link('https://doi.org/10.1111/j.2517-6161.1995.tb02031.x', 'Benjamini and Hochberg (1995)')}: false discovery rate control across segments.</li>
        <li>{link('https://kellogg.northwestern.edu/faculty/gordon_b/files/fb_comparison.pdf', 'Observational vs randomized ad measurement')} (Gordon et al.): why attribution overstates.</li>
      </ul>
      <h3>Data</h3>
      <ul>
        <li>
          {link('https://blog.minethatdata.com/2008/03/minethatdata-e-mail-analytics-and-data.html', 'Hillstrom MineThatData e-mail challenge')} (2008)
          and {link('https://stochasticsolutions.com/pdf/HillstromChallenge.pdf', "Radcliffe's analysis")}.
        </li>
        <li>{link('https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/margin.html', 'Damodaran margins by sector')}.</li>
      </ul>
      <h3>Code</h3>
      <p>{link('https://github.com/advaithvemurisai/retail-ab-lab', 'github.com/advaithvemurisai/retail-ab-lab')}</p>
    </div>
  )
}
