# Linux Server Configuration w/ SSH Access

## About this project:
Brief introduction to setting up an instance on AWS and securing access through SSH

## Details
### Access points
* IP address:   52.40.8.107
* SSH Port:     2200
* URL:          http://ec2-52-40-8-107.us-west-2.compute.amazonaws.com/

### Installed Software and Configurations
* Updated/upgraded all pre-installed software packages
* Configured AWS provided firewall and UFW to only allow incoming connections for SSH (port 2200), HTTP (port 80), and NTP (port 123)
* Created grader user, granted sudo access, installed public key, set permissions on .ssh and authorized key directories
* Limited login to SSH only (prohibit password access)
* Timezone was already configured by default
* Installed apache, postgres, pip, Flask, flask-cli, httplib2, google-api-python-client, sqlalchemy, psycopg2, werkzeug
* Downloaded catalog app and packaged as module
* Initialized DB, created catalog as user, granted all neccesary permissions

### Third Party Resources
* http://drumcoder.co.uk/blog/2010/nov/12/apache-environment-variables-and-mod_wsgi/
* https://www.digitalocean.com/community/tutorials/how-to-deploy-a-flask-application-on-an-ubuntu-vps
* https://postgresapp.com/ (for local dev)
* https://realpython.com/blog/python/flask-by-example-part-2-postgres-sqlalchemy-and-alembic/
* http://killtheyak.com/use-postgresql-with-django-flask/
