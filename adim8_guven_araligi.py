import simpy
import random
import statistics
import matplotlib.pyplot as plt

ISLEM_SURELERI = [2.5, 3.0, 4.0, 2.8, 3.2]
N_ISTASYON = len(ISLEM_SURELERI)
MTBF = 60
MTTR = 8

def simulasyon_calistir(tampon_kapasitesi, sure=480):
    tamamlanan_parca_sayisi = 0
    env = simpy.Environment()

    def parca_uretici(env, giris_tamponu):
        i = 0
        while True:
            yield env.timeout(random.expovariate(1/4))
            i += 1
            yield giris_tamponu.put((f"Parca-{i}", env.now))

    def ariza_sureci(env, idx, ariza_durumu):
        while True:
            yield env.timeout(random.expovariate(1/MTBF))
            ariza_durumu[idx] = True
            yield env.timeout(random.expovariate(1/MTTR))
            ariza_durumu[idx] = False

    def istasyon_sureci(env, idx, giris_tamponu, cikis_tamponu, ariza_durumu):
        nonlocal tamamlanan_parca_sayisi
        while True:
            isim, varis = yield giris_tamponu.get()
            while ariza_durumu[idx]:
                yield env.timeout(0.5)
            yield env.timeout(ISLEM_SURELERI[idx])
            if cikis_tamponu is not None:
                yield cikis_tamponu.put((isim, varis))
            else:
                tamamlanan_parca_sayisi += 1

    tamponlar = [simpy.Store(env)] + [simpy.Store(env, capacity=tampon_kapasitesi) for _ in range(N_ISTASYON - 1)]
    ariza_durumu = [False] * N_ISTASYON

    env.process(parca_uretici(env, tamponlar[0]))
    for idx in range(N_ISTASYON):
        giris = tamponlar[idx]
        cikis = tamponlar[idx + 1] if idx < N_ISTASYON - 1 else None
        env.process(istasyon_sureci(env, idx, giris, cikis, ariza_durumu))
        env.process(ariza_sureci(env, idx, ariza_durumu))

    env.run(until=sure)
    return tamamlanan_parca_sayisi / (sure / 60)

TEKRAR_SAYISI = 10
tampon_degerleri = []
ortalamalar = []
guven_araliklari = []

for tampon_kapasitesi in range(1, 11):
    sonuclar = [simulasyon_calistir(tampon_kapasitesi) for _ in range(TEKRAR_SAYISI)]
    ortalama = statistics.mean(sonuclar)
    sapma = statistics.stdev(sonuclar)
    guven_araligi = 1.96 * sapma / (TEKRAR_SAYISI ** 0.5)

    tampon_degerleri.append(tampon_kapasitesi)
    ortalamalar.append(ortalama)
    guven_araliklari.append(guven_araligi)

    print(f"Tampon kapasitesi={tampon_kapasitesi:2d}  ortalama throughput={ortalama:5.2f} parca/saat  (95% GA: ±{guven_araligi:.2f})")

en_iyi_index = ortalamalar.index(max(ortalamalar))
en_iyi_tampon = tampon_degerleri[en_iyi_index]
en_iyi_throughput = ortalamalar[en_iyi_index]

print()
print(f"EN IYI: Tampon kapasitesi={en_iyi_tampon}  ortalama throughput={en_iyi_throughput:.2f} parca/saat")

plt.figure(figsize=(9, 5))
alt_sinir = [o - g for o, g in zip(ortalamalar, guven_araliklari)]
ust_sinir = [o + g for o, g in zip(ortalamalar, guven_araliklari)]
plt.fill_between(tampon_degerleri, alt_sinir, ust_sinir, alpha=0.2, label="95% guven araligi")
plt.plot(tampon_degerleri, ortalamalar, marker="o")
plt.scatter([en_iyi_tampon], [en_iyi_throughput], color="red", zorder=5, label=f"En iyi: {en_iyi_tampon}")
plt.xlabel("Tampon kapasitesi (istasyonlar arasi)")
plt.ylabel("Ortalama throughput (parca/saat)")
plt.title("Tampon kapasitesine gore uretim hatti throughput'u (95% guven araligi)")
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("tampon_optimizasyon_grafigi.png")
print("Grafik kaydedildi: tampon_optimizasyon_grafigi.png")