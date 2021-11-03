# Setup #

`docker-compose up -d`

In the `mysql` container:
1. `sudo userdel mysql`
2. `sudo useradd -u 999 mysql`

On your host machine:
1. `sudo mkdir -p /data/mysql`
2. `sudo chown -R mysql:mysql /data/mysql`

In the `wordpress` container:
1. `deluser www-data`
2. `adduser -u 82 www-data`

On your host machine:
1. `mkdir -p ./data/html`
2. `sudo chown -R www-data:www-data /data/html`

Import posts: 
Tools -> Import -> Wordpress (Install Now) Wordpress -> Import