import simpy
import random

ISLEM_SURELERI = [2.5, 3.0, 4.0, 2.8, 3.2]  # dakika, her istasyon icin (istasyon 3 kasitli olarak en yavas)
TAMPON_KAPASITESI = 3
N_ISTASYON = len(ISLEM_SURELERI)

istasyon_mesgul = [0.0] * N_ISTASYON
istasyon_bloke = [0.0] * N_ISTASYON
tamamlanan_parca_sayisi = 0
sistemde_gecen_sureler = []

def parca_uretici(env, giris_tamponu):
    i = 0
    while True:
        yield env.timeout(random.expovariate(1/4))
        i += 1
        yield giris_tamponu.put((f"Parca-{i}", env.now))

def istasyon_sureci(env, idx, giris_tamponu, cikis_tamponu):
    global tamamlanan_parca_sayisi
    while True:
        isim, varis = yield giris_tamponu.get()
        baslangic = env.now
        yield env.timeout(ISLEM_SURELERI[idx])
        istasyon_mesgul[idx] += env.now - baslangic

        if cikis_tamponu is not None:
            bloke_baslangic = env.now
            yield cikis_tamponu.put((isim, varis))
            istasyon_bloke[idx] += env.now - bloke_baslangic
        else:
            sistemde_gecen_sureler.append(env.now - varis)
            tamamlanan_parca_sayisi += 1

SIMULASYON_SURESI = 480

env = simpy.Environment()
# ilk tampon (giris) sinirsiz, aradaki tamponlar sinirli kapasiteli
tamponlar = [simpy.Store(env)] + [simpy.Store(env, capacity=TAMPON_KAPASITESI) for _ in range(N_ISTASYON - 1)]

env.process(parca_uretici(env, tamponlar[0]))
for idx in range(N_ISTASYON):
    giris = tamponlar[idx]
    cikis = tamponlar[idx + 1] if idx < N_ISTASYON - 1 else None
    env.process(istasyon_sureci(env, idx, giris, cikis))

env.run(until=SIMULASYON_SURESI)

throughput_saatlik = tamamlanan_parca_sayisi / (SIMULASYON_SURESI / 60)

print(f"Tamamlanan parca sayisi: {tamamlanan_parca_sayisi}")
print(f"Ortalama sistemde gecen sure: {sum(sistemde_gecen_sureler)/len(sistemde_gecen_sureler):.2f} dakika")
print(f"Throughput: {throughput_saatlik:.1f} parca/saat")
print()
for idx in range(N_ISTASYON):
    print(f"Istasyon {idx+1} (islem suresi={ISLEM_SURELERI[idx]} dk): "
          f"isleme orani=%{istasyon_mesgul[idx]/SIMULASYON_SURESI*100:5.1f}  "
          f"bloke orani=%{istasyon_bloke[idx]/SIMULASYON_SURESI*100:5.1f}")

en_yogun_istasyon = max(range(N_ISTASYON), key=lambda i: istasyon_mesgul[i])
print()
print(f"DARBOGAZ: Istasyon {en_yogun_istasyon + 1} (en yuksek isleme orani)")