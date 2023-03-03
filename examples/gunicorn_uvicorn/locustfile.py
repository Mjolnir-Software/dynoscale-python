from locust import HttpUser, between, task, tag


class WebsiteUser(HttpUser):
    wait_time = between(3, 15)

    def on_start(self):
        self.client.get("/")

    @task(5)
    def index(self):
        self.client.get("/")

    @task(10)
    def date(self):
        self.client.get("/date")

    @task(10)
    def info(self):
        self.client.get("/info")

    @tag('io')
    @task(3)
    def io_1(self):
        self.client.get("/io/1")

    @tag('cpu')
    @task(3)
    def cpu_1(self):
        self.client.get("/cpu/1")

    @tag('ram')
    @task(3)
    def ram_1(self):
        self.client.get("/ram/1")

    @tag('gc')
    @task(3)
    def gc_1(self):
        self.client.get("/gc/1")

    @tag('io')
    @task
    def io_5(self):
        self.client.get("/io/5")

    @tag('cpu')
    @task
    def cpu_5(self):
        self.client.get("/cpu/5")

    @tag('ram')
    @task
    def ram_5(self):
        self.client.get("/ram/5")

    @tag('gc')
    @task()
    def gc_5(self):
        self.client.get("/gc/5")
