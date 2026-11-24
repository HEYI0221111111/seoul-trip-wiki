---
title: 操作紀錄
type: log
---

# 操作紀錄

> 只能往後追加，不可改寫。標題格式：`## [YYYY-MM-DD] 操作類型 | 標題`

## [2026-11-23] schema | 建立首爾旅遊攻略 Wiki
- 與使用者討論後確定 CLAUDE.md：給台灣旅客的通用攻略，主題為美食、購物逛街、傳統文化與市場、韓國必買
- 不收錄住宿、咖啡廳、K-pop 與韓劇景點
- 建立資料夾結構、頁面範本、web/ 網站產生器

## [2026-11-23] collect | 第一輪上網蒐集
- 在 raw/web/ 建立 10 份來源摘要：入境與 K-ETA、退稅、交通與機場、網路與換錢、潮牌、包包與鞋子、美妝零食、市場、古宮與北村、商圈
- 只存網址、日期與自己整理的重點，不存原文

## [2026-11-23] ingest | 第一輪精簡版收錄（47 頁）
- 新建：實用資訊 8 頁、比較 1 頁、市場 5 頁、品牌 7 頁、購物地點 3 頁、必買 6 頁、區域 9 頁、傳統文化 3 頁、美食 1 頁、行程範本 4 頁
- 更新：[[index]]、[[overview]]
- 待查證：K-ETA 2027 年後是否延長、通仁市場平日營業時間、MARITHÉ 明洞店營業時間、Matin Kim 創立年份、北村週日限制、景福宮日間開放與休宮日
- 單一來源：鞋子品牌、部分包包品牌與美妝單品

## [2026-11-23] collect | 首爾韓式烤肉
- 新增 raw/web/2026-11-23_韓式烤肉.md：米其林指南、Creatrip、uptogo、Dcard、食神、polle、Travelko、首爾市 Media Hub、bring-you、Seoul Tourism、Klook、Pelago、funliday

## [2026-11-23] ingest | 首爾韓式烤肉
- 新建：[[金豬食堂]]、[[肉典食堂]]、[[黃金牧場]]
- 更新：[[首爾必吃料理]]（新增韓式烤肉段落）、[[明洞]]、[[東大門]]、[[index]]、[[overview]]
- 待查證：金豬食堂套餐價格日期與是否可訂位；肉典食堂本店開店時間、價格、新設洞站出口；黃金牧場營業時間與價格
- 單一來源：荒謬的生肉、一片里脊（只在 [[首爾必吃料理]] 帶過）

## [2026-11-23] web | build.py 支援 OneDrive 唯讀資料夾
- 清空 docs/ 時，遇到唯讀的檔案或資料夾會先解除唯讀再刪除，避免 OneDrive 同步資料夾造成 PermissionError

## [2026-11-24] ingest | 延南洞特色小店攻略（跟著漫琳去旅行）
- 新增 raw/web/2026-11-24_延南洞小店_跟著漫琳去旅行.md、raw/web/2026-11-24_延南洞_交叉查證.md
- 更新：[[弘大與延南洞]]（新增延南洞選物店表、3 號出口與林蔭道交通、延南洞半日逛法）、[[韓系包包]]（加入 CARLYN）、[[index]]
- 未建新頁：14 間店都只有這一篇文章介紹，地址與營業時間都查不到，未達建頁門檻
- 待查證：CARLYN 延南旗艦店地址、fwee AGIT 延南店地址、所有延南店家的營業時間
- 另做延南洞逛街示意地圖（claude.ai Artifact，不在網站內；網站地圖依 web/CLAUDE.md 暫不做）

## [2026-11-24] collect | 延南洞店家第二輪查證
- 新增 raw/web/2026-11-24_延南洞_第二輪查證.md：fwee 官網、CARLYN 開幕新聞、各店官方 Instagram、welfarehello、yogikorea、Threads、Konest、Cosmopolitan HK

## [2026-11-24] ingest | 延南洞店家第二輪查證
- 新建：[[Hetras]]、[[fwee AGIT 延南]]
- 更新：[[弘大與延南洞]]（店家表分成「已查到地址」與「還查不到地址」、逛法改依地址排序）、[[韓系包包]]（CARLYN 新旗艦店地址）、[[韓國美妝]]（FWEE 改為 2 個來源）、[[index]]
- 已查到地址：fwee AGIT 延南、CARLYN 弘大旗艦店、Geulliming Day、Daol Sangjeom、taag 延南、Blue Elephant 延南展示間
- 待查證：Hetras 弘大店門牌；漫琳寫的「Hetras 延南」「CARLYN 延南旗艦店」是否就是弘大店
- 仍查不到：SCENTORA、DARK SPECTER、JUUNEEDU、VISUAL AID、自然島鹽麵包延南店
- 延南洞逛街地圖同步更新

## [2026-11-24] ingest | 聖水洞、漢南洞 Threads 逛街清單
- 新增 raw/web/2026-11-24_聖水漢南_Threads清單.md（@lizon_konkuk 聖水 12 家、@roolez553 漢南 17 家）、raw/web/2026-11-24_聖水漢南_交叉查證.md
- 更新：[[聖水洞逛街動線]]（新增韓系女裝店表，路線改依門牌由西往東）、[[聖水洞]]、[[漢南洞]]（香氛保養、服飾選物分表，交通改以漢江鎮站 3 號出口為起點）、[[index]]
- 已查證：GENERAL IDEA、sienne、LOW CLASSIC、TILL I DIE（聖水）；Tamburins、BEAKER、NONFICTION（漢南）
- 單一來源：聖水 emis、The Barnnet、SUARE WEST、rolarola、RAIVE；漢南其餘 13 家
- 待查證：TILL I DIE 兩種地址寫法；NONFICTION 營業時間來自 2020 年公告

## [2026-11-24] web | 延南洞逛街地圖改用實際座標
- 依 OpenStreetMap（Nominatim、Overpass）座標重畫地圖：加上楊花路、延南路、동교로46길、京義線林蔭道、東津市場、弘大入口站、方位與 100 m 比例尺
- 店家改成 6 個依建議順序編號的站點；地圖仍是 claude.ai Artifact，不在網站內

## [2026-11-24] web | 聖水洞、漢南洞沿街示意地圖
- 這次無法連線 OpenStreetMap，改依道路名地址規則（門牌約每號 10 公尺、單雙號分兩側）畫沿街示意圖：聖水洞以練武場街為主軸，漢南洞以梨泰院路 229～255 號為主軸，小巷與地址待查的店另列
- 地圖是 claude.ai Artifact，不在網站內
- 修正：[[聖水洞逛街動線]] 與 [[index]] 先前寫「門牌由西往東遞增」，方位未經查證，改為「照門牌順序」

## [2026-11-24] web | 聖水洞、漢南洞地圖改成街道地圖
- OpenStreetMap 恢復連線後，依使用者提供的參考圖做法（街道底圖加店家標記）重畫兩張地圖：道路、鐵路、公園、車站出口來自 OSM；店家點位依門牌沿街推算，用 OSM 門牌點校正
- 聖水洞：聖水站與 2 號線在練武場街北邊，練武場街門牌由西南往東北遞增；연무장11길、17길都往北岔出
- 漢南洞：梨泰院路門牌由西南（梨泰院站）往東北（漢江鎮站）遞增；이태원로55가길在梨泰院路西北側
- 兩張地圖共用 map.css、map.js；仍是 claude.ai Artifact，不在網站內

## [2026-11-24] collect | 弘大晚餐餐廳、AREX 普通車票價
- 新增 raw/web/2026-11-24_弘大餐廳與AREX票價.md（Trip.com、Bella、Creatrip、NAMANE、uptogo）
- 更新：[[弘大與延南洞]]（新增弘大晚餐：申美京辣炒雞排、一片鰻魚、荒謬的生肉）、[[機場到市區]]（普通車到弘大入口不到 ₩5,000）
- 用途：三天兩夜投影片（slides/首爾三天兩夜/）第一天晚餐與預算頁

## [2026-11-24] web | 發布到 GitHub
- 建立公開 repo：https://github.com/heyi0221111/seoul-trip-wiki （commit 作者使用 GitHub noreply 信箱）
- 開啟 GitHub Pages（main 分支 /docs）：https://heyi0221111.github.io/seoul-trip-wiki/
- raw/articles/ 依 .gitignore 不上傳
