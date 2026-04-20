# B556_project

1. First create the database by running the queries in [ERD.sql](ERD.sql)

2. Download Pixi into your Linux machine using

```bash
curl -fsSL https://pixi.sh/install.sh | sh
```

3. If you use windows, run this command in Windows Powershell
```bash
powershell -ExecutionPolicy ByPass -c "irm -useb https://pixi.sh/install.ps1 | iex"
```

4. In your workspace, run this command to create your environment

```bash
cd /your/workspace/B556_project
pixi init
pixi add django mysqlclient pymysql python-decouple
```

5. Create your .env file with the below variables storing your connection variables

```bash
SECRET_KEY=your-secret-key-here
DEBUG=True
DB_NAME=fertility_clinic
DB_USER=root
DB_PASSWORD=your_pwd
DB_HOST=127.0.0.1
DB_PORT=3306
```

6. Run this command to generate synthea data after installing [Docker-Desktop](https://www.docker.com/products/docker-desktop/)

```bash
docker run --rm -v "${PWD}/data:/output" --name synthea-docker intersystemsdc/irisdemo-base-synthea:version-1.3.4 -p 800 --seed 42 --generate.only_alive_patients=true -a 20-50
```

7. Download these datasets from Kaggle

[Dataset 1](https://www.kaggle.com/datasets/gabbygab/fertility-data-set)
[Dataset 2](https://www.kaggle.com/datasets/echekwuelijah/fertility-and-menstrual-health-data)
[Dataset 3](https://www.kaggle.com/datasets/stevenhicks/visem-video-dataset)

8. Generate migrations for the patients
```bash
pixi run python manage.py makemigrations patients
```

9. Migrate your database to Django by running this command

```bash
pixi run python manage.py migrate
```

10.  Append data to the database using this command

```bash
pixi run python load_synthea.py
```

11. To create admin access, run this
```bash
pixi run python manage.py createsuperuser
```

12. Start the server by running this command
```bash
pixi run python manage.py runserver
```
