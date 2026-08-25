import simpy
import random

ISLEM_SURELERI = [2.5, 3.0, 4.0, 2.8, 3.2]
N_ISTASYON = len(ISLEM_SURELERI)
MTBF = 60
MTTR = 8

def simulasyon_calistir(tampon_kapasitesi, sure=480):
    istasyon_mesgul = [0.0] * N_ISTASYON
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
            baslangic = env.now
            yield env.timeout(ISLEM_SURELERI[idx])
            istasyon_mesgul[idx] += env.now - baslangic
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

for tampon_kapasitesi in range(1, 11):
    throughput = simulasyon_calistir(tampon_kapasitesi)
    print(f"Tampon kapasitesi={tampon_kapasitesi:2d}  Throughput={throughput:5.1f} parca/saat")