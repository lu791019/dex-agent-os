## 元資料
- 發布日期：2025-02-28
- 互動數據：❤️ 7 💬 3 🔄 0 👁️ 1289
- 表現評估：低互動
- 連結：https://www.threads.com/@daydreamdex/post/DGm6pa-zlY2

## 原文
持續來分享工作上的學習了！與上次 Physics-informed 的 PINN 不同，這次要來試試以Data-Driven 方式的 3D U-Net！

這既是對 3D U-Net 在 CFD（計算流體力學）應用的整理，希望能幫助到有相同困惑的你，一起討論和交流吧

🚀 為什麼要做 Data-Driven 3D U-Net？
傳統的 CFD（Computational Fluid Dynamics）流體模擬，像 OpenFOAM、Ansys 等，雖然物理精確，但難以即時應用。Data-Driven 方法則是透過深度學習：

- 加速流體預測
- 減少對高階 CFD 模擬工具的依賴（降低門檻）
- 提供更即時的設計迭代（適用於我們議題：散熱系統等）

不同的是，我們希望是讓 3D U-Net 透過 STL（3D 幾何）+ 熱力圖（溫度資訊）作為Input，來預測流體物理場，希望完全用 AI 來模擬流場分布

想了解的，留言處繼續介紹3D UNet，以及和2D UNet應用的差異
