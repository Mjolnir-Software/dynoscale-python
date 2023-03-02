from locust import HttpUser, between, task


class WebsiteUser(HttpUser):
    wait_time = between(3, 15)

    def on_start(self):
        # self.client.post(
        #     "/login", {
        #         "username": "test_user",
        #         "password": ""
        #     }
        # )
        pass

    @task
    def index(self):
        self.client.get("/")

    @task
    def cpu(self):
        self.client.get("/cpu/1")

    @task
    def ram(self):
        self.client.get("/ram/1")

    @task
    def io(self):
        self.client.get("/io/1")
