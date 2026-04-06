# B556_project

1. Download Pixi into your Linux machine using

```bash
curl -fsSL https://pixi.sh/install.sh | sh
```

2. If you use windows, run this command in Windows Powershell
```bash
powershell -ExecutionPolicy ByPass -c "irm -useb https://pixi.sh/install.ps1 | iex"
```

3. In your workspace, run this command to create your environment

```bash
cd /your/workspace/B556_project
pixi init
pixi add django mysqlclient pymysql python-decouple
```

4. Create your .env file with the below variables storing your connection variables

```bash
SECRET_KEY=your-secret-key-here
DEBUG=True
DB_NAME=fertility_clinic
DB_USER=root
DB_PASSWORD=your_pwd
DB_HOST=127.0.0.1
DB_PORT=3306
```

5. Migrate your database to Django by running this command

```bash
pixi run python manage.py migrate
```

6. To create admin access, run this
```bash
pixi run python manage.py createsuperuser
```

7. Start the server by running this command
```bash
pixi run python manage.py runserver
```