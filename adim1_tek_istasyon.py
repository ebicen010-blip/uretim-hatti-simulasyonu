import simpy
import random

def parca_uretici(env, istasyon):
    i = 0
    while True:
        yield env.timeout(random.expovariate(1/4))  # ortalama 4 dakikada bir parca geliyor
        i += 1
        env.process(parca_isle(env, f"Parca-{i}", istasyon))

def parca_isle(env, isim, istasyon):
    varis = env.now
    print(f"{isim} hatta girdi: t={varis:.1f}")
    with istasyon.request() as istek:
        yield istek
        bekleme = env.now - varis
        print(f"{isim} istasyona girdi: t={env.now:.1f} (bekledi: {bekleme:.1f} dk)")
        yield env.timeout(3)  # islem suresi sabit 3 dakika
        print(f"{isim} istasyondan cikti: t={env.now:.1f}")

env = simpy.Environment()
istasyon = simpy.Resource(env, capacity=1)
env.process(parca_uretici(env, istasyon))
env.run(until=30)
