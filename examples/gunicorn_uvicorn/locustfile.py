from locust import HttpUser, between, task, tag


class WebsiteUser(HttpUser):
    wait_time = between(3, 15)

    def on_start(self):
        self.client.get("/")

    @task(10)
    def index(self):
        self.client.get("/")

    @tag('cpu')
    @task(3)
    def cpu_1(self):
        self.client.get("/cpu/1")

    @tag('ram')
    @task(4)
    def ram_1(self):
        self.client.get("/ram/1")

    @tag('io')
    @task(4)
    def io_1(self):
        self.client.get("/io/1")

    @tag('cpu')
    @task
    def cpu_2(self):
        self.client.get("/cpu/2")

    @tag('ram')
    @task
    def ram_2(self):
        self.client.get("/ram/2")

    @tag('io')
    @task
    def io_2(self):
        self.client.get("/io/2")
