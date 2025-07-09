import subprocess, time, requests, os, signal, pytest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
BACKEND_APP = REPO_ROOT / "backend_mock" / "app.py"
FRONTEND_APP = REPO_ROOT / "frontend_py" / "app.py"

BACKEND_URL = "http://localhost:5050"
FRONTEND_URL = "http://localhost:5006"


def _wait_until_ready(url: str, timeout: int = 15) -> bool:
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(url, timeout=1)
            if r.status_code < 500:  # 200 or auth redirect is fine for readiness
                return True
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(0.5)
    return False


@pytest.fixture(scope="session", autouse=True)
def _servers():
    """Spin up backend and frontend Flask servers for the entire test session.

    Having a single place avoids duplication across backend_mock/ and frontend_py/
    conftest files and ensures *all* tests (including those located at repo root)
    see the same servers.
    """
    # Kill any stale processes that might block the ports (best-effort)
    subprocess.run(["pkill", "-f", str(BACKEND_APP)], stderr=subprocess.DEVNULL)
    subprocess.run(["pkill", "-f", str(FRONTEND_APP)], stderr=subprocess.DEVNULL)

    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"

    backend_proc = subprocess.Popen(["python3", str(BACKEND_APP)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    if not _wait_until_ready(f"{BACKEND_URL}/api/health", timeout=20):
        out, err = backend_proc.communicate(timeout=2)
        raise RuntimeError(f"Backend failed to start.\nSTDOUT:\n{out.decode()}\nSTDERR:\n{err.decode()}")

    frontend_proc = subprocess.Popen(["python3", str(FRONTEND_APP)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    if not _wait_until_ready(FRONTEND_URL, timeout=20):
        out, err = frontend_proc.communicate(timeout=2)
        backend_proc.terminate()
        raise RuntimeError(f"Frontend failed to start.\nSTDOUT:\n{out.decode()}\nSTDERR:\n{err.decode()}")

    print("\n[TEST] Backend & frontend servers running for test session.\n")
    yield  # tests run here

    # Tear down processes
    for proc in (frontend_proc, backend_proc):
        proc.send_signal(signal.SIGTERM)
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
