import simpy
import random

TAMPON_KAPASITESI = 3  # istasyon 1 ile istasyon 2 arasindaki bekleme alani (kac parca sigar)

istasyon1_mesgul = 0
istasyon1_bloke = 0
istasyon2_mesgul = 0
tamamlanan_parca_sayisi = 0
sistemde_gecen_sureler = []

def parca_uretici(env, istasyon1, tampon):
    i = 0
    while True:
        yield env.timeout(random.expovariate(1/4))
        i += 1
        env.process(istasyon1_isle(env, f"Parca-{i}", istasyon1, tampon))

def istasyon1_isle(env, isim, istasyon1, tampon):
    global istasyon1_mesgul, istasyon1_bloke
    varis = env.now
    with istasyon1.request() as istek:
        yield istek
        baslangic = env.now
        yield env.timeout(3)  # islem suresi
        istasyon1_mesgul += env.now - baslangic

        # islem bitti ama tampon dolu olabilir -> parcayi birakamiyoruz, BLOKE oluyoruz
        bloke_baslangic = env.now
        yield tampon.put((isim, varis))
        istasyon1_bloke += env.now - bloke_baslangic

def istasyon2_surec(env, tampon):
    global istasyon2_mesgul, tamamlanan_parca_sayisi
    while True:
        isim, varis = yield tampon.get()
        baslangic = env.now
        yield env.timeout(2.5)
        istasyon2_mesgul += env.now - baslangic
        sistemde_gecen_sureler.append(env.now - varis)
        tamamlanan_parca_sayisi += 1

SIMULASYON_SURESI = 480

env = simpy.Environment()
istasyon1 = simpy.Resource(env, capacity=1)
tampon = simpy.Store(env, capacity=TAMPON_KAPASITESI)
env.process(parca_uretici(env, istasyon1, tampon))
env.process(istasyon2_surec(env, tampon))
env.run(until=SIMULASYON_SURESI)

throughput_saatlik = tamamlanan_parca_sayisi / (SIMULASYON_SURESI / 60)

print(f"Tamamlanan parca sayisi: {tamamlanan_parca_sayisi}")
print(f"Ortalama sistemde gecen sure: {sum(sistemde_gecen_sureler)/len(sistemde_gecen_sureler):.2f} dakika")
print(f"Throughput: {throughput_saatlik:.1f} parca/saat")
print(f"Istasyon 1 isleme orani: %{istasyon1_mesgul/SIMULASYON_SURESI*100:.1f}")
print(f"Istasyon 1 bloke orani (tampon dolu, bekliyor): %{istasyon1_bloke/SIMULASYON_SURESI*100:.1f}")
print(f"Istasyon 2 isleme orani: %{istasyon2_mesgul/SIMULASYON_SURESI*100:.1f}")