import streamlit as st
import simpy
import random
import statistics
import pandas as pd

st.set_page_config(page_title="Uretim Hatti Simulasyonu", layout="centered")

st.set_page_config(page_title="Üretim Hattı Simülasyonu", page_icon="🏭", layout="wide")

st.title("Üretim Hattı Simülasyonu")
st.markdown(
    "Beş istasyonlu bir üretim hattını simüle eder ve iki farklı senaryoyu "
    "(tampon kapasitesi, arıza sıklığı, varış hızı) karşılaştırmanı sağlar."
)
st.divider()

st.sidebar.header("Senaryo A")
tampon_a = st.sidebar.slider("Tampon kapasitesi (A)", 1, 15, 5, key="tampon_a")
mtbf_a = st.sidebar.slider("MTBF - dakika (A)", 20, 200, 60, key="mtbf_a")
mttr_a = st.sidebar.slider("MTTR - dakika (A)", 2, 30, 8, key="mttr_a")
varis_a = st.sidebar.slider("Ortalama varis araligi (A)", 1.0, 10.0, 4.0, key="varis_a")

st.sidebar.header("Senaryo B")
tampon_b = st.sidebar.slider("Tampon kapasitesi (B)", 1, 15, 8, key="tampon_b")
mtbf_b = st.sidebar.slider("MTBF - dakika (B)", 20, 200, 60, key="mtbf_b")
mttr_b = st.sidebar.slider("MTTR - dakika (B)", 2, 30, 8, key="mttr_b")
varis_b = st.sidebar.slider("Ortalama varis araligi (B)", 1.0, 10.0, 4.0, key="varis_b")

st.sidebar.header("Genel")
tekrar_sayisi = st.sidebar.slider("Tekrar sayisi", 1, 20, 5, key="tekrar")

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

if st.sidebar.button("Senaryolari Karsilastir"):
    with st.spinner("Simüle ediliyor..."):
        sonuclar_a = [simulasyon_calistir(tampon_a, mtbf_a, mttr_a, varis_a) for _ in range(tekrar_sayisi)]
        sonuclar_b = [simulasyon_calistir(tampon_b, mtbf_b, mttr_b, varis_b) for _ in range(tekrar_sayisi)]

        throughput_a = [s[0] for s in sonuclar_a]
        throughput_b = [s[0] for s in sonuclar_b]

        ortalama_a = statistics.mean(throughput_a)
        ortalama_b = statistics.mean(throughput_b)

        guven_a = 1.96 * statistics.stdev(throughput_a) / (len(throughput_a) ** 0.5) if len(throughput_a) > 1 else 0.0
        guven_b = 1.96 * statistics.stdev(throughput_b) / (len(throughput_b) ** 0.5) if len(throughput_b) > 1 else 0.0

        kol_a, kol_b = st.columns(2)

        with kol_a:
            st.subheader("Senaryo A")
            st.metric("Ortalama Throughput", f"{ortalama_a:.2f} parça/saat", f"±{guven_a:.2f} (95% GA)")

        with kol_b:
            st.subheader("Senaryo B")
            st.metric("Ortalama Throughput", f"{ortalama_b:.2f} parça/saat", f"±{guven_b:.2f} (95% GA)")

        st.subheader("Throughput Karşılaştırması")
        karsilastirma_df = pd.DataFrame(
            {"Throughput (parça/saat)": [ortalama_a, ortalama_b]},
            index=["Senaryo A", "Senaryo B"]
        )
        st.bar_chart(karsilastirma_df)

        fark_yuzde = (ortalama_b - ortalama_a) / ortalama_a * 100
        if fark_yuzde > 0:
            st.success(f"Kazanan: Senaryo B — Senaryo A'ya göre **%{fark_yuzde:.1f}** daha fazla throughput sağlıyor.")
        elif fark_yuzde < 0:
            st.success(f"Kazanan: Senaryo A — Senaryo B'ye göre **%{abs(fark_yuzde):.1f}** daha fazla throughput sağlıyor.")
        else:
            st.info("İki senaryo da aynı throughput'u veriyor.")     
        st.subheader("İstasyon Doluluk Oranları (Son Çalıştırma)")
        son_utilization_a = sonuclar_a[-1][1]
        son_utilization_b = sonuclar_b[-1][1]

        utilization_df = pd.DataFrame(
            {
                "Senaryo A": [u * 100 for u in son_utilization_a],
                "Senaryo B": [u * 100 for u in son_utilization_b],
            },
            index=[f"İstasyon {i+1}" for i in range(len(son_utilization_a))]
        )
        st.bar_chart(utilization_df, stack=False)
        en_yogun_a = max(range(len(son_utilization_a)), key=lambda i: son_utilization_a[i])
        en_yogun_b = max(range(len(son_utilization_b)), key=lambda i: son_utilization_b[i])

        kol_a2, kol_b2 = st.columns(2)
        with kol_a2:
            st.info(f"Senaryo A darboğazı: İstasyon {en_yogun_a + 1} (%{son_utilization_a[en_yogun_a]*100:.1f} doluluk)")
        with kol_b2:
            st.info(f"Senaryo B darboğazı: İstasyon {en_yogun_b + 1} (%{son_utilization_b[en_yogun_b]*100:.1f} doluluk)")

        ozet_df = pd.DataFrame({
            "Senaryo": ["Senaryo A", "Senaryo B"],
            "Throughput (parça/saat)": [ortalama_a, ortalama_b],
            "Guven Araligi (95%)": [guven_a, guven_b],
            "Istasyon 1 Doluluk (%)": [son_utilization_a[0]*100, son_utilization_b[0]*100],
            "Istasyon 2 Doluluk (%)": [son_utilization_a[1]*100, son_utilization_b[1]*100],
            "Istasyon 3 Doluluk (%)": [son_utilization_a[2]*100, son_utilization_b[2]*100],
            "Istasyon 4 Doluluk (%)": [son_utilization_a[3]*100, son_utilization_b[3]*100],
            "Istasyon 5 Doluluk (%)": [son_utilization_a[4]*100, son_utilization_b[4]*100],
        })

        st.download_button(
            label="Sonuçları CSV olarak indir",
            data=ozet_df.to_csv(index=False).encode("utf-8-sig"),
            file_name="senaryo_karsilastirma_sonuclari.csv",
            mime="text/csv"
        )

st.divider()
st.caption("Bu uygulama SimPy ile geliştirilen bir üretim hattı simülasyonudur. Kaynak kod: github.com/ebicen010-blip/uretim-hatti-simulasyonu")