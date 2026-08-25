import simpy
import random

bekleme_sureleri = []
tamamlanan_parca_sayisi = 0
istasyon_mesgul_suresi = 0

def parca_uretici(env, istasyon):
    i = 0
    while True:
        yield env.timeout(random.expovariate(1/4))
        i += 1
        env.process(parca_isle(env, f"Parca-{i}", istasyon))

def parca_isle(env, isim, istasyon):
    global tamamlanan_parca_sayisi, istasyon_mesgul_suresi
    varis = env.now
    with istasyon.request() as istek:
        yield istek
        bekleme = env.now - varis
        bekleme_sureleri.append(bekleme)
        baslangic = env.now
        yield env.timeout(3)  # islem suresi
        istasyon_mesgul_suresi += env.now - baslangic
        tamamlanan_parca_sayisi += 1

SIMULASYON_SURESI = 480  # 8 saatlik bir vardiya (dakika cinsinden)

env = simpy.Environment()
istasyon = simpy.Resource(env, capacity=1)
env.process(parca_uretici(env, istasyon))
env.run(until=SIMULASYON_SURESI)

throughput_saatlik = tamamlanan_parca_sayisi / (SIMULASYON_SURESI / 60)
doluluk_orani = istasyon_mesgul_suresi / SIMULASYON_SURESI

print(f"Tamamlanan parca sayisi: {tamamlanan_parca_sayisi}")
print(f"Ortalama bekleme suresi: {sum(bekleme_sureleri)/len(bekleme_sureleri):.2f} dakika")
print(f"Throughput: {throughput_saatlik:.1f} parca/saat")
print(f"Istasyon doluluk orani (utilization): %{doluluk_orani*100:.1f}")