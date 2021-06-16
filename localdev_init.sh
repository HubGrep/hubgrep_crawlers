#!/bin/bash
# this is a localdev script for populating the DB with a working set of platforms
# - NOT for production or auto crawling!

set -a; source .env; set +a

flask cli db-create
flask cli db-init

flask cli add-platform github 'https://api.github.com' --auth_data "{\"access_token\": \"$GITHUB_TOKEN\"}"

: '
python crawler.py add-platform gitlab 'https://gitlab.com/'

python crawler.py add-platform gitea 'https://codeberg.org/'
python crawler.py add-platform gitea 'https://git.spip.net/'
python crawler.py add-platform gitea 'https://gitea.com/'
python crawler.py add-platform gitea 'https://git.teknik.io/'
python crawler.py add-platform gitea 'https://opendev.org/'
python crawler.py add-platform gitea 'https://gitea.codi.coop/'
python crawler.py add-platform gitea 'https://git.osuv.de/'
python crawler.py add-platform gitea 'https://git.koehlerweb.org/'
python crawler.py add-platform gitea 'https://gitea.vornet.cz/'
python crawler.py add-platform gitea 'https://git.luehne.de/'
python crawler.py add-platform gitea 'https://djib.fr/'
python crawler.py add-platform gitea 'https://code.antopie.org/'
python crawler.py add-platform gitea 'https://git.daiko.fr/'
python crawler.py add-platform gitea 'https://gitea.anfuchs.de/'
python crawler.py add-platform gitea 'https://git.sablun.org/'
python crawler.py add-platform gitea 'https://git.jcg.re/'

'


