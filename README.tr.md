[![GitHub release](https://img.shields.io/github/v/release/sametbrr/prompt-architect?display_name=tag&sort=semver)](https://github.com/sametbrr/prompt-architect/releases/latest)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Agent Skills](https://img.shields.io/badge/agentskills.io-compatible-blue)](https://agentskills.io)

[Hızlı Başlangıç](#hızlı-başlangıç) • [Özellikler](#özellikler) • [Kurulum](#kurulum) • [Kullanım](#kullanım) • [Nasıl Çalışır](#nasıl-çalışır) • [Sınırlamalar](#sınırlamalar)

# Prompt Architect

Her türlü ham fikri; alan sınıflandırmalı, modele duyarlı ve kalite denetiminden geçmiş uzman prompt'a dönüştüren bir Agent Skill. Türkçe ve İngilizce girdi kabul eder.

> 🇬🇧 For English see [README.md](README.md)

---

## Hızlı Başlangıç

```bash
git clone https://github.com/sametbrr/prompt-architect.git ~/.claude/skills/prompt-architect
```

Claude Code oturumunu yeniden başlat, sonra doğal şekilde tetikle:

```
> "Şunu uzman prompt'a çevir: B2B SaaS için onboarding stratejisi kur"
```

---

## Özellikler

| Özellik | Ne yapar |
|---|---|
| Hedef model çözümleme | Aktif Claude modelini ve effort seviyesini oturumdan okur ya da açık hedefi alır. Bulamazsa `opus-5`'e düşer |
| Modele özel ayarlama | Prompt bloklarını modele göre ekler, çıkarır veya kısaltır — Opus 5 conciseness bloğu alır ve doğrulama talimatı almaz, Fable 5 daha hafif bir iskelet alır |
| Alan sınıflandırma | Girdiyi 25 alanlık taksonomiye karşı Türkçe ve İngilizce sinyal kelimelerle eşler |
| Pattern seçimi | 14 prompting pattern'inden göreve yeten en küçük alt kümeyi seçer |
| İki iskelet | Basit görevler için kompakt madde gövdesi, karmaşık görevler için tam XML gövdesi |
| 11 kapılı öz-denetim | Yedi evrensel kapı, artı hedef modele göre davranışı değişen dört kapı |
| İki dilli girdi | Türkçe veya İngilizce girer; taşınabilirlik için prompt gövdesi her zaman İngilizce çıkar |
| İsteğe bağlı yürütme | Çıktıyı üretir ve yapılandırılmış sonucu dosyaya yazar — yalnızca istendiğinde |

Prompt gövdesi her zaman İngilizce yazılır. Bölüm etiketleri kullanıcının girdi diline uyar.

---

## Gereksinimler

- Python 3.10+ — iki script için. Yalnızca standart kütüphane, `pip install` gerekmez
- Claude Code veya [agentskills.io](https://agentskills.io) uyumlu herhangi bir ajan

Model tespiti Claude Code oturum transcript'ini okur. Diğer ajanlar skill'i yine çalıştırır; varsayılan model profiline düşerler.

---

## Kurulum

```bash
git clone https://github.com/sametbrr/prompt-architect.git ~/.claude/skills/prompt-architect
```

Claude Code, `~/.claude/skills/` altındaki skill'leri otomatik keşfeder. Klonladıktan sonra oturumu yeniden başlat.

Projeye özel kurulum için deponun içindeki `.claude/skills/` dizinine klonla.

### Kaldırma

```bash
rm -rf ~/.claude/skills/prompt-architect
```

Skill kendi dizini dışına hiçbir şey yazmaz — hook yok, config dosyası yok, PATH değişikliği yok. Dizini silmek tam kaldırma demektir.

---

## Kullanım

```bash
# Taslak prompt'u kalite kapılarına karşı doğrula
python3 scripts/validate_prompt.py --stdin --target-model opus-5 < draft-prompt.txt

# Mevcut oturumdan aktif modeli ve effort'u çöz
python3 scripts/detect_model.py

# Her iki script için yerleşik testleri çalıştır
python3 scripts/validate_prompt.py --self-test
python3 scripts/detect_model.py --self-test
```

### Modlar

| İstediğin… | Şuna benzer bir şey söyle… | Mod |
|---|---|---|
| Sadece düzenlenmiş prompt | `sadece prompt`, `prompt yaz yeter`, `çalıştırma` | `prompt_only` (varsayılan) |
| Prompt + gerçek çıktı | `çalıştır`, `execute et`, `sonucu da üret` | `prompt_and_execute` |

### Belirli bir modeli hedefleme

Skill hedefi şu sırayla çözer: senin belirttiğin açık hedef, sonra oturum modeli, sonra `opus-5`.

```
> "Bu prompt'u Opus 4.8 için yaz: çeyreklik finansalları özetle"
> "Fable 5'e göre ayarla"
```

Tanınmayan bir model, jenerik tavsiyeye değil `opus-5` profiline düşer — güncel bir amiral gemi profili, bilinmeyen yeni bir modele hiç profil olmamasından daha iyi uyar.

### `validate_prompt.py`

Prompt'u kalite kapılarına karşı puanlar, başarısızlıkta sıfırdan farklı çıkış kodu döner.

```bash
python3 scripts/validate_prompt.py draft.txt --target-model fable-5
```

| Bayrak | Amaç |
|---|---|
| `--stdin` | Prompt'u standart girdiden oku |
| `--target-model` | `opus-5` (varsayılan), `opus-4-8`, `sonnet-5`, `fable-5` değerlerinden biri |
| `--self-test` | Yerleşik vakaları çalıştırır; tersine çevrilen kapıların gerçekten tetiklendiğini de kanıtlar |

1–6 ve 8. kapılar her zaman geçerlidir. 7, 9, 10 ve 11. kapılar hedefe göre davranış değiştirir; bu yüzden skor `N/N` biçimindedir ve `N` geçerli kapı sayısıdır.

### `detect_model.py`

Aktif modeli JSON olarak yazdırır. Yalnızca yerel dosya okuma — ağ yok, cache dosyası yok, hook yok.

```bash
$ python3 scripts/detect_model.py
{"id": "claude-opus-5", "effort": "xhigh", "profile": "opus-5", "source": "session", "transcript": "..."}
```

Okunabilir bir transcript yoksa `{"source": "default", "profile": "opus-5"}` döner ve 0 ile çıkar — modelin tespit edilememesi hata değil, normal bir sonuçtur.

### Örnek

**Girdi:**
> B2B SaaS için onboarding stratejisi kur, çalıştır da

**Çıktı (kısaltılmış):**

```
Target Model: Opus 5 (detected from session · effort: xhigh) — profile: opus-5
Detected Domain: Product Growth Strategy
Complexity: moderate
Selected Patterns: Role, XML Structuring, Positive Guidance, Scope Boundaries,
                   Verbosity Control, Output Framing
Model-Specific Adjustments: conciseness block added; scope_boundaries added;
                   verification instruction deliberately omitted (Opus 5 over-verifies)

Refined English Prompt:
<role>You are a senior product growth strategist...</role>
<task>Design a B2B SaaS onboarding strategy...</task>
...

Self-Review: 11/11 gates passed
Final Output: Saved to ./onboarding-strategy-output.md
```

---

## Nasıl Çalışır

Yedi aşama sırayla işler. Aşama 0 kendinden sonraki her şeyi belirler; çünkü hangi pattern'lerin geçerli olacağına ve hangi kalite kapılarının tetikleneceğine hedef model karar verir.

| Aşama | Ne olur |
|---|---|
| 0 — Hedef Modeli Çöz | Açık hedef → oturum tespiti → `opus-5`. Yönlendirme matrisini, ortak canon'u ve tek bir model profilini yükler |
| 1 — Analiz | Amaç, kısıtlar ve karmaşıklık skoru (basit / orta / karmaşık) |
| 2 — Alan Sınıflandırma | 25 alanlık taksonomiden tek baskın alan, çıktıyı biçimlendiriyorsa bir de destekleyici alan |
| 3 — Pattern Seçimi | 14 pattern'in göreve yeten en küçük alt kümesi; hem göreve hem hedef modele göre süzülür |
| 4 — Taslak | Kompakt veya XML iskelet, eşleşen alan paketiyle zenginleştirilir |
| 5 — Öz-Denetim | Geçerli kapılar, ardından tek bir revizyon turu |
| 6 — Yürütme | Yalnızca `prompt_and_execute` modunda |

Kaç model desteklenirse desteklensin her çalıştırmada üç dosya yüklenir: yönlendirme matrisi, ortak canon ve tek profil. Profil eklendikçe bağlam maliyeti sabit kalır.

### Model profilleri

| Profil | Belirleyici davranış |
|---|---|
| `opus-5` ★ varsayılan | Uzun yazar ve `effort` görünür çıktı uzunluğunu kısaltmaz; bu yüzden özlük açıkça istenmeli. Kendi işini doğrular — doğrulama talimatı eklemek aşırı doğrulamaya yol açar |
| `opus-4-8` | Uzunluğu görev karmaşıklığına göre ayarlar. `xhigh` effort ile başla, en az `high` |
| `sonnet-5` | `opus-4-8`'e en yakın olan; ancak effort zaten `high` varsayılanında ve kaynak kılavuzda subagent bölümü yok |
| `fable-5` | Mythos 5'i de kapsar. Akıl yürütmesini yazdırmasını asla isteme ve iskeleti hafif tut — fazla kuralcı prompt'lar çıktısını düşürür |

---

## Proje Yapısı

```
prompt-architect/
├── SKILL.md                          # Skill giriş noktası + 7 aşamalı akış
├── references/
│   ├── models/
│   │   ├── _matrix.md                # Yönlendirme + davranış matrisi (her zaman okunur)
│   │   ├── _shared-canon.md          # Modelden bağımsız canon (her zaman okunur)
│   │   └── {opus-5,opus-4-8,sonnet-5,fable-5}.md
│   ├── claude-prompting-patterns.md  # 14 pattern + harness seviyesi kontroller
│   ├── quality-gates.md              # 11 kapı, 4'ü modele koşullu
│   ├── domain-taxonomy.md            # 25 alan, TR + EN sinyaller
│   ├── mode-inference.md             # prompt_only ve prompt_and_execute ayrımı
│   └── claude-md-rules.md            # Çift katmanlı uygulanan yazım kuralları
├── assets/templates/
│   ├── refined-prompt-xml.tmpl       # XML iskelet (orta/karmaşık görevler)
│   ├── refined-prompt-compact.tmpl   # Madde iskeleti (basit görevler, Fable 5)
│   └── domain-*.tmpl                 # 6 alan paketi
└── scripts/
    ├── detect_model.py               # Oturum modeli + effort çözümleme
    └── validate_prompt.py            # Kalite kapısı doğrulayıcı (yalnız stdlib)
```

---

## Sınırlamalar

- **Model ayarlaması yalnızca Anthropic için.** Düzenlenmiş prompt'lar GPT, Gemini ve diğer modellerde çalışmaya devam eder, ancak sağlayıcıya özel bir ayar taşımaz. Anthropic dışı bir hedef belirttiğinde skill jenerik biçimi üretir ve başka bir sağlayıcının davranışını tahmin etmek yerine bunu açıkça söyler.
- **Profiller kendini tazelemez.** Her biri köken bilgisi olarak bir `last_verified` tarihi taşır; hiçbir şey bunu kontrol etmez veya güncellemez. Anthropic'in dokümanları hızlı değişiyor — Temmuz 2026'da 12 günde 125 URL değişti, `adaptive-thinking` silindi, prefill 400'e döndü. Önemli olduğunda profilleri elle yeniden türet ve tarihi güncelle. Karşılığında skill'in çalışma anında hiç ağ bağımlılığı olmaz.
- **Model tespiti Claude Code'a özgü.** `detect_model.py` Claude Code oturum transcript'ini okur. Diğer ajanlar varsayılan profile düşer; bu bir hata değil, amaçlanan davranıştır. Aynı dizinde birden çok eşzamanlı oturum varsa "en son değişen" seçimi yanlış transcript'i seçebilir — önemliyse hedefi açıkça belirt.
- **Kapı denetimleri sezgiseldir.** Regex ve yapısal tarama; yaygın eksikleri ucuza yakalamak için tasarlandı. Prompt'u okumanın yerini tutmaz.

---

## Sorun Giderme

**Skill tetiklenmiyor** — Dizinin `~/.claude/skills/prompt-architect` konumunda ve `SKILL.md` dosyasının kökünde olduğunu doğrula, sonra oturumu yeniden başlat. Skill'ler başlangıçta keşfedilir.

**`detect_model.py` sürekli `"source": "default"` dönüyor** — Ya Claude Code içinde çalışmıyorsun ya da mevcut çalışma dizini için henüz bir transcript yok. Bunun yerine hedef modeli isteğinde açıkça belirt.

**v2.x altında geçen bir prompt artık kalıyor** — Beklenen durum. v3.0.0, 7. kapıyı tersine çevirdi ve 9–11. kapıları ekledi. `<scratchpad>` direktifi, "review your output" hatırlatıcısı veya eksik bir kapsam bloğu artık işaretlenir. Her birinin gerekçesi için [CHANGELOG](CHANGELOG.md) dosyasına bak.

**`validate_prompt.py` 11'den az kapı sayısı bildiriyor** — Doğru davranış. 9. kapı yalnızca `opus-5`, 11. kapı yalnızca `opus-5` ve `fable-5` için geçerlidir; bu yüzden payda hedefe göre değişir.

---

## Lisans

MIT — [LICENSE](LICENSE) dosyasına bak.

---

<div align="center">
<a href="https://github.com/sametbrr/prompt-architect/issues">Hata Bildir</a> ·
<a href="https://github.com/sametbrr/prompt-architect/issues">Özellik Öner</a>
</div>
