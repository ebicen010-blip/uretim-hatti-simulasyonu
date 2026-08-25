import simpy
import random

istasyon1_mesgul = 0
istasyon2_mesgul = 0
tamamlanan_parca_sayisi = 0
sistemde_gecen_sureler = []

def parca_uretici(env, istasyon1, istasyon2):
    i = 0
    while True:
        yield env.timeout(random.expovariate(1/4))
        i += 1
        env.process(parca_isle(env, f"Parca-{i}", istasyon1, istasyon2))

def parca_isle(env, isim, istasyon1, istasyon2):
    global istasyon1_mesgul, istasyon2_mesgul, tamamlanan_parca_sayisi
    varis = env.now

    with istasyon1.request() as istek1:
        yield istek1
        baslangic = env.now
        yield env.timeout(3)  # istasyon 1 islem suresi (orn. kesim)
        istasyon1_mesgul += env.now - baslangic

    with istasyon2.request() as istek2:
        yield istek2
        baslangic = env.now
        yield env.timeout(2.5)  # istasyon 2 islem suresi (orn. montaj)
        istasyon2_mesgul += env.now - baslangic

    sistemde_gecen_sureler.append(env.now - varis)
    tamamlanan_parca_sayisi += 1

SIMULASYON_SURESI = 480

env = simpy.Environment()
istasyon1 = simpy.Resource(env, capacity=1)
istasyon2 = simpy.Resource(env, capacity=1)
env.process(parca_uretici(env, istasyon1, istasyon2))
env.run(until=SIMULASYON_SURESI)

throughput_saatlik = tamamlanan_parca_sayisi / (SIMULASYON_SURESI / 60)

print(f"Tamamlanan parca sayisi: {tamamlanan_parca_sayisi}")
print(f"Ortalama sistemde gecen sure: {sum(sistemde_gecen_sureler)/len(sistemde_gecen_sureler):.2f} dakika")
print(f"Throughput: {throughput_saatlik:.1f} parca/saat")
print(f"Istasyon 1 doluluk orani: %{istasyon1_mesgul/SIMULASYON_SURESI*100:.1f}")
print(f"Istasyon 2 doluluk orani: %{istasyon2_mesgul/SIMULASYON_SURESI*100:.1f}")