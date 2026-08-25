import streamlit as st
import simpy
import random
import statistics

st.set_page_config(page_title="Uretim Hatti Simulasyonu", layout="centered")

st.title("Üretim Hattı Simülasyonu")
st.write("Parametreleri soldan değiştir, simülasyonu anında yeniden çalıştır.")

st.sidebar.header("Parametreler")
tampon_kapasitesi = st.sidebar.slider("Tampon kapasitesi", 1, 15, 5)
mtbf = st.sidebar.slider("MTBF (dakika)", 20, 200, 60)
mttr = st.sidebar.slider("MTTR (dakika)", 2, 30, 8)
varis_araligi = st.sidebar.slider("Ortalama varis araligi (dakika)", 1.0, 10.0, 4.0)
tekrar_sayisi = st.sidebar.slider("Tekrar sayisi", 1, 20, 5)

ISLEM_SURELERI = [2.5, 3.0, 4.0, 2.8, 3.2]
N_ISTASYON = len(ISLEM_SURELERI)

def simulasyon_calistir(tampon_kapasitesi, mtbf, mttr, varis_araligi, sure=480):
    tamamlanan_parca_sayisi = 0
    istasyon_mesgul = [0.0] * N_ISTASYON
    env = simpy.Environment()

    def parca_uretici(env, giris_tamponu):
        i = 0
        while True:
            yield env.timeout(random.expovariate(1 / varis_araligi))
            i += 1
            yield giris_tamponu.put((f"Parca-{i}", env.now))

    def ariza_sureci(env, idx, ariza_durumu):
        while True:
            yield env.timeout(random.expovariate(1 / mtbf))
            ariza_durumu[idx] = True
            yield env.timeout(random.expovariate(1 / mttr))
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
    throughput = tamamlanan_parca_sayisi / (sure / 60)
    utilization = [m / sure for m in istasyon_mesgul]
    return throughput, utilization

if st.sidebar.button("Simülasyonu Çalıştır"):
    with st.spinner("Simüle ediliyor..."):
        sonuclar = [simulasyon_calistir(tampon_kapasitesi, mtbf, mttr, varis_araligi) for _ in range(tekrar_sayisi)]
        throughputlar = [s[0] for s in sonuclar]
        ortalama = statistics.mean(throughputlar)
        guven_araligi = 1.96 * statistics.stdev(throughputlar) / (len(throughputlar) ** 0.5) if len(throughputlar) > 1 else 0.0

        st.metric("Ortalama Throughput", f"{ortalama:.2f} parça/saat", f"±{guven_araligi:.2f} (95% GA)")

        son_utilization = sonuclar[-1][1]
        st.subheader("İstasyon Doluluk Oranları (%)")
        st.bar_chart({f"İstasyon {i+1}": u * 100 for i, u in enumerate(son_utilization)})

        en_yogun = max(range(N_ISTASYON), key=lambda i: son_utilization[i])
        st.info(f"Darboğaz: İstasyon {en_yogun + 1} (%{son_utilization[en_yogun]*100:.1f} doluluk)")
        