import json
from django.test import TestCase, Client
from django.urls import reverse
from pyspark.sql import SparkSession
from pyspark.ml import PipelineModel


class BaseSpamPredictTest(TestCase):
    """Общий класс для тестов предсказаний."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.spark = (
            SparkSession.builder
            .appName("TestSpamFilter")
            .master("local[*]")
            .getOrCreate()
        )
        cls.client = Client()

    @classmethod
    def tearDownClass(cls):
        cls.spark.stop()
        super().tearDownClass()

    def setUp(self):
        # Подменяем глобальную переменную model в модуле Filter.views
        import Filter.views as views_module
        views_module.model = self.model

    def _post_message(self, message: str) -> dict:
        # reverse('predict') даст правильный URL без ручного указания префикса
        url = reverse("predict")
        response = self.client.post(
            url,
            data=json.dumps({"message": message}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200, f"Status not 200 for message: {message}")
        return response.json()

    def _check_success_structure(self, data: dict):
        print(data)
        self.assertEqual(data.get("status"), "success")
        self.assertIn("result", data)
        self.assertIn("probability", data)
        self.assertIn(data["result"], ["SPAM", "NOT SPAM"])
        self.assertIsInstance(data["probability"], float)
        self.assertGreaterEqual(data["probability"], 0.0)
        self.assertLessEqual(data["probability"], 1.0)


class LREnglishModelTest(BaseSpamPredictTest):
    MODEL_PATH = "spam_filter/models/spam_model_lr"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.model = PipelineModel.load(cls.MODEL_PATH)

    def test_spam_english(self):
        spam_messages = [
            "Buy cheap watches now!",
            "Congratulations! You won a lottery prize!",
            "FREE viagra online! Click here now.",
            "Make money fast! Work from home.",
            "Your bank account is suspended! Verify immediately.",
        ]
        for msg in spam_messages:
            with self.subTest(msg=msg):
                data = self._post_message(msg)
                self._check_success_structure(data)
                self.assertEqual(data["result"], "SPAM")

    def test_ham_english(self):
        ham_messages = [
            "Hello, how are you?",
            "Are we still meeting tomorrow?",
            "Can you send the report by EOD?",
            "Let's grab lunch together.",
            "I attached the document you requested.",
        ]
        for msg in ham_messages:
            with self.subTest(msg=msg):
                data = self._post_message(msg)
                self._check_success_structure(data)
                self.assertEqual(data["result"], "NOT SPAM")


class LRRuModelTest(BaseSpamPredictTest):
    MODEL_PATH = "spam_filter/models/spam_model_lr_ru"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.model = PipelineModel.load(cls.MODEL_PATH)

    def test_spam_russian(self):
        spam_messages = [
            "Купите часы со скидкой 90% только сегодня!",
            "Поздравляем! Вы выиграли 1 000 000 рублей!",
            "Увеличьте продажи в 10 раз – проверенный метод.",
            "Ваш аккаунт заблокирован, перейдите по ссылке для восстановления.",
            "Бесплатные онлайн-курсы только для вас, регистрируйтесь сейчас!",
        ]
        for msg in spam_messages:
            with self.subTest(msg=msg):
                data = self._post_message(msg)
                self._check_success_structure(data)
                self.assertEqual(data["result"], "SPAM")

    def test_ham_russian(self):
        ham_messages = [
            "Привет, как дела?",
            "Давай встретимся завтра в 10 утра.",
            "Скинь, пожалуйста, отчёт по проекту.",
            "Позвони мне, когда освободишься.",
            "Сегодня отличная погода для прогулки.",
        ]
        for msg in ham_messages:
            with self.subTest(msg=msg):
                data = self._post_message(msg)
                self._check_success_structure(data)
                self.assertEqual(data["result"], "NOT SPAM")


class LRRuBigModelTest(BaseSpamPredictTest):
    MODEL_PATH = "spam_filter/models/spam_model_lr_ru_big"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.model = PipelineModel.load(cls.MODEL_PATH)

    def test_spam_russian_big(self):
        spam_messages = [
            "Только сегодня! Скидки до 80% на все товары.",
            "Заработайте от 50 000 рублей в день без вложений!",
            "Срочно! Ваш номер участвует в розыгрыше приза.",
            "Лучшее предложение по кредитам под 0% годовых.",
            "Уникальная методика похудения без диет и спорта.",
        ]
        for msg in spam_messages:
            with self.subTest(msg=msg):
                data = self._post_message(msg)
                self._check_success_structure(data)
                self.assertEqual(data["result"], "SPAM")

    def test_ham_russian_big(self):
        ham_messages = [
            "Привет! Ты не забыл про нашу встречу?",
            "Пришли мне фотографии с субботы.",
            "Как дела с подготовкой презентации?",
            "Давай в эти выходные съездим на дачу.",
            "Я прочитал твою статью, очень интересно.",
        ]
        for msg in ham_messages:
            with self.subTest(msg=msg):
                data = self._post_message(msg)
                self._check_success_structure(data)
                self.assertEqual(data["result"], "NOT SPAM")


class SVMRuModelTest(BaseSpamPredictTest):
    MODEL_PATH = "spam_filter/models/spam_model_svm_ru"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.model = PipelineModel.load(cls.MODEL_PATH)

    def test_spam_russian_svm(self):
        spam_messages = [
            "Поможем получить кредит без справок и поручителей!",
            "Акция! Только сегодня – бесплатный сыр при покупке вина.",
            "Ваш IP-адрес заблокирован, переведите 1$ для разблокировки.",
            "Вы стали победителем в нашей лотерее!",
            "Доход до 200 000 рублей в месяц, работая по 2 часа в день.",
        ]
        for msg in spam_messages:
            with self.subTest(msg=msg):
                data = self._post_message(msg)
                self._check_success_structure(data)
                self.assertEqual(data["result"], "SPAM")

    def test_ham_russian_svm(self):
        ham_messages = [
            "Привет, давай сегодня вечером поиграем в футбол?",
            "Напомни, во сколько завтра собрание отдела?",
            "Я отправлял тебе документ, проверь почту.",
            "Как прошёл твой отпуск? Расскажи!",
            "Сегодня в офисе отключают свет с 14:00.",
        ]
        for msg in ham_messages:
            with self.subTest(msg=msg):
                data = self._post_message(msg)
                self._check_success_structure(data)
                self.assertEqual(data["result"], "NOT SPAM")