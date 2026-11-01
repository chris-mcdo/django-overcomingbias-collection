"""Run with unittest; REDIS_TEST_HOST enables disposable-server integration."""
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from huey import PriorityRedisHuey
from huey.serializer import Serializer
from redis import Redis
from redis.exceptions import AuthenticationError, NoPermissionError

from obcollection.security import configure_redis

SPEC = importlib.util.spec_from_file_location(
    "prepare_secrets", Path(__file__).resolve().parents[1] / "deploy/security/prepare_redis_secrets.py"
)
prepare_secrets = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(prepare_secrets)


class SecurityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.directory = Path(os.environ.get("REDIS_TEST_SECRETS", Path(self.tmp.name) / "private"))
        if "REDIS_TEST_SECRETS" not in os.environ:
            prepare_secrets.prepare(self.directory)
        self.namespace = {"HUEY": {"name": "obcollection", "huey_class": "huey.PriorityRedisHuey",
                                    "immediate": False, "consumer": {"workers": 4}}}
        configure_redis(self.namespace, self.directory, os.environ.get("REDIS_TEST_HOST", "localhost"))

    def test_fail_closed_without_secrets(self):
        with self.assertRaises(FileNotFoundError):
            configure_redis(self.namespace, Path(self.tmp.name) / "absent")

    def test_signing_rejects_unsigned_and_modified_before_unpickling(self):
        serializer = self.namespace["HUEY"]["serializer"]
        self.assertEqual(serializer.deserialize(serializer.serialize({"value": 1})), {"value": 1})
        unsigned = Serializer().serialize({"value": 1})
        signed = serializer.serialize({"value": 1})
        with patch("huey.serializer.pickle.loads") as loads:
            for value in [unsigned, b"changed" + signed]:
                with self.assertRaises(ValueError):
                    serializer.deserialize(value)
            loads.assert_not_called()

    def test_cache_clients_are_separate_and_scoped(self):
        caches = self.namespace["CACHES"]
        self.assertNotEqual(caches["default"]["OPTIONS"]["password"], caches["select2"]["OPTIONS"]["password"])
        self.assertEqual(caches["default"]["KEY_PREFIX"], "obcollection-cache")
        self.assertEqual(caches["select2"]["KEY_PREFIX"], "obcollection-select2")
        self.assertEqual(self.namespace["HUEY"]["consumer"], {"workers": 4})

    @unittest.skipUnless(os.environ.get("REDIS_TEST_HOST"), "disposable Redis integration only")
    def test_redis_acl_queue_schedule_results_and_caches(self):
        host = os.environ["REDIS_TEST_HOST"]
        with self.assertRaises(AuthenticationError):
            Redis(host=host).ping()
        config = self.namespace["HUEY"]
        huey = PriorityRedisHuey(name=config["name"], serializer=config["serializer"],
                                 **config["connection"])
        @huey.task()
        def add(left, right):
            return left + right

        result = add(2, 3)
        huey.execute(huey.dequeue())
        self.assertEqual(result.get(), 5)
        store = huey.storage
        message = huey.serializer.serialize({"test": "signed"})
        store.enqueue(message)
        self.assertEqual(huey.serializer.deserialize(store.dequeue()), {"test": "signed"})
        import datetime
        now = datetime.datetime.now()
        store.add_to_schedule(message, now)
        self.assertEqual(store.read_schedule(now), [message])
        store.put_data(b"test-result", message)
        self.assertEqual(store.pop_data(b"test-result"), message)
        for alias, config in self.namespace["CACHES"].items():
            from django.core.cache.backends.redis import RedisCache
            # Settings are not needed for standalone cache instances.
            cache = RedisCache(config["LOCATION"], {"KEY_PREFIX": config["KEY_PREFIX"],
                                                     "OPTIONS": config["OPTIONS"]})
            cache.set("audit", 1, 60)
            self.assertEqual(cache.get("audit"), 1)
            cache.set_many({"a": 2, "b": 3})
            self.assertEqual(cache.get_many(["a", "b"]), {"a": 2, "b": 3})
            self.assertEqual(cache.incr("audit"), 2)
            self.assertTrue(cache.touch("audit", 30))
            self.assertTrue(cache.touch("audit", None))
            cache.delete_many(["a", "b", "audit"])
            client = Redis(host=host, username=config["OPTIONS"]["username"],
                           password=config["OPTIONS"]["password"])
            with self.assertRaises(NoPermissionError):
                client.zadd("huey.redis.obcollection", {b"unsigned": 0})
            with self.assertRaises(NoPermissionError):
                client.config_get("*")
        with self.assertRaises(NoPermissionError):
            store.conn.set("obcollection-cache:1:other", "forbidden")
        with self.assertRaises(NoPermissionError):
            store.conn.flushall()


if __name__ == "__main__":
    unittest.main()
