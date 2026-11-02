[![GitHub release](https://img.shields.io/github/v/release/sametbrr/prompt-architect?display_name=tag&sort=semver)](https://github.com/sametbrr/prompt-architect/releases/latest)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Agent Skills](https://img.shields.io/badge/agentskills.io-compatible-blue)](https://agentskills.io)

[Hızlı Başlangıç](#hızlı-başlangıç) • [Özellikler](#özellikler) • [Kurulum](#kurulum) • [Kullanım](#kullanım) • [Nasıl Çalışır](#nasıl-çalışır) • [Sınırlamalar](#sınırlamalar)

# Prompt Architect

Claude Code ve OpenAI Codex için bir Agent Skill ve eklenti. Ham bir fikri alan sınıflandırmalı, modele duyarlı ve kalite denetiminden geçmiş uzman prompt'a dönüştürür. Hangi host ve modelde çalıştığını tespit eder, prompt'u Claude veya OpenAI modellerine göre ayarlar. Türkçe ve İngilizce girdi kabul eder.

> 🇬🇧 For English see [README.md](README.md)

---

## Hızlı Başlangıç

```bash
claude plugin marketplace add sametbrr/skill-hub
claude plugin install prompt-architect@skill-hub
```

Sonra Claude Code'da veya Codex'te doğal şekilde tetikle:

```
> "Turn this into an expert prompt: build an onboarding strategy for a B2B SaaS"
> "Write this prompt for GPT-6.1 Sol: add rate limiting to /search"
```

---

## Özellikler

| Özellik | Ne yapar |
|---|---|
| Host + model tespiti | Claude Code'u veya Codex'i tanır, aktif modeli ve effort seviyesini yerel oturum dosyasından okur. Açık hedef her zaman kazanır |
| Claude profilleri | Opus 5.5 (varsayılan), Sonnet 5.5, Haiku 5.5, Fable 5.1 / Mythos 5.1; ayrıca eski Opus 5, Sonnet 5, Opus 4.8 ve Fable 5 |
| OpenAI profilleri | Canlı model kataloğundan Codex katmanları: Sol (gpt-6.1-sol, gpt-6-sol, gpt-5.6-sol), Astra (gpt-6-astra), Terra (gpt-6.1-terra, gpt-5.6-terra), Luna (gpt-6-luna, gpt-5.6-luna) |
| Modele özel ayarlama | Opus 5.5 kapsam bloğu alır, doğrulama satırı almaz; Sonnet/Haiku 5.5 tamamlama ve gerçek kontrol satırları alır; Fable 5.1 hafif iskelet alır; Codex modelleri kısıtlar, done-when ve kontrol komutu içeren markdown bölümleri alır |
| Alan sınıflandırma | Girdiyi 25 alanlık taksonomiye karşı Türkçe ve İngilizce sinyal kelimelerle eşler |
| Pattern seçimi | 14 prompting pattern'inden göreve yeten en küçük alt kümeyi seçer |
| Üç iskelet | Basit görevler için kompakt madde, karmaşık Claude prompt'ları için XML, Codex için markdown bölümleri |
| 12 kapılı öz-denetim | Uygulanmayan kapılar N/A olarak raporlanır, asla geçti sayılmaz |
| İki dilli girdi | Türkçe veya İngilizce girer; prompt gövdesi her zaman İngilizce çıkar |
| İsteğe bağlı yürütme | Çıktıyı üretir ve yapılandırılmış sonucu dosyaya yazar, yalnızca istendiğinde |

---

## Gereksinimler

- Python 3.10+, iki script için. Yalnızca standart kütüphane, `pip install` gerekmez
- Claude Code, Codex veya [agentskills.io](https://agentskills.io) uyumlu herhangi bir ajan

Model tespiti Claude Code oturum transcript'ini veya Codex rollout dosyasını okur. Diğer ajanlar skill'i yine çalıştırır; açık hedefi veya generic profili kullanırlar.

---

## Kurulum

```bash
# Claude Code
claude plugin marketplace add sametbrr/skill-hub
claude plugin install prompt-architect@skill-hub
# Codex
codex plugin marketplace add sametbrr/skill-hub
codex plugin add prompt-architect@skill-hub
# Manuel (herhangi bir Agent Skills istemcisi): skills/prompt-architect klasörünü ~/.claude/skills/ veya ~/.agents/skills/ altına kopyala
```

Kurduktan sonra oturumu yeniden başlat; skill'ler açılışta keşfedilir.

### Kaldırma

```bash
claude plugin uninstall prompt-architect@skill-hub   # Claude Code
codex plugin remove prompt-architect@skill-hub       # Codex
```

Manuel kurulumda kopyaladığın `prompt-architect` klasörünü sil. Skill, senin istediğin dosyalar dışında hiçbir şey yazmaz: hook yok, config yok, cache yok.

---

## Kullanım

Script'leri `skills/prompt-architect/` içinden çalıştır:

```bash
# Taslak prompt'u kalite kapılarına karşı doğrula
python3 scripts/validate_prompt.py --stdin --target-model opus-5-5 < draft-prompt.txt
python3 scripts/validate_prompt.py draft.md --target-model gpt-6.1-sol

# Aktif host, model ve effort'u ya da açık bir hedefi çözümle
python3 scripts/detect_model.py
python3 scripts/detect_model.py --model "Sonnet 5.5"

# Yerleşik testler
python3 scripts/validate_prompt.py --self-test
python3 scripts/detect_model.py --self-test
```

### Modlar

| İstediğin… | Şöyle bir şey söyle… | Mod |
|---|---|---|
| Sadece rafine prompt | `sadece prompt`, `prompt yaz yeter`, `execute etme` | `prompt_only` (varsayılan) |
| Prompt + asıl çıktı | `çalıştır`, `uygula`, `sonucu da üret` ya da çıktıya yönelik bir emir: `strateji hazırla`, `domain analizi yap` | `prompt_and_execute` |

### Belirli bir modeli hedefleme

Skill hedefi şu sırayla çözer: senin söylediğin açık hedef, sonra tespit edilen oturum modeli, sonra host varsayılanı (Claude Code'da `opus-5-5`, Codex'te `gpt-sol`, diğer yerlerde `generic`).

```
> "Write this prompt for Haiku 5.5: classify support tickets"
> "GPT-6 Astra için ayarla"
> "Codex için AGENTS.md kuralı yaz: testleri her zaman çalıştır"
```

Bilinmeyen yeni Claude modelleri Opus 5.5 profilini, bilinmeyen GPT modelleri Sol profilini bir notla kullanır. Diğer sağlayıcılar (Gemini, Llama…) ayarlanmamış generic formu alır.

### `detect_model.py`

Tek bir JSON nesnesi yazdırır. Yalnızca yerel dosya okur, ağ yok.

```bash
$ python3 scripts/detect_model.py
{"host": "claude-code", "model": "claude-opus-5-5", "effort": "high", "source": "session",
 "family": "claude", "profile": "opus-5-5",
 "profile_files": ["references/models/_matrix.md", "references/models/_shared-canon.md", "references/models/opus-5-5.md"], ...}
```

Tespit sırası: `PROMPT_ARCHITECT_MODEL` / `PROMPT_ARCHITECT_EFFORT` override → Codex (`CODEX_THREAD_ID`, rollout dosyasındaki son `turn_context`, sonra `config.toml`) → Claude Code (`CLAUDE_CONFIG_DIR` veya `~/.claude` altındaki `CLAUDE_CODE_SESSION_ID` transcript'i, effort `CLAUDE_EFFORT`'tan) → bilinmeyen host. İki host'un değişkenleri birlikte varsa, oturum dosyası en son yazılan host kazanır. Oturum dosyaları sondan okunur, bozuk satırlar atlanır.

### `validate_prompt.py`

| Bayrak | Amaç |
|---|---|
| `--stdin` | Prompt'u standart girdiden oku |
| `--target-model` | Bir profil (`opus-5-5`, `sonnet-5-5`, `haiku-5-5`, `fable-5-1`, `gpt-sol`, `gpt-astra`, `gpt-terra`, `gpt-luna`, `generic`, eski profil adları) ya da `gpt-5.6-terra` gibi herhangi bir model ID'si. Varsayılan `opus-5-5` |
| `--self-test` | Yerleşik test vakalarını çalıştır |

Her kapı PASS, FAIL, WARN veya N/A raporlar. Skor `geçen / uygulanan` şeklindedir; N/A kapılar listelenir ama sayılmaz. Herhangi bir kapı kalırsa çıkış kodu 1'dir.

### Örnek

**Girdi:**
> B2B SaaS için onboarding stratejisi kur, ve çalıştır

**Çıktı (kısaltılmış):**

```
Target Model: Opus 5.5 (detected · host: claude-code · effort: high) — profile: opus-5-5
Detected Domain: Product Growth Strategy
Complexity: moderate
Selected Patterns: Role, XML Structuring, Positive Guidance, Scope Boundaries,
                   Verbosity Control, Output Framing
Model-Specific Adjustments: scope_boundaries added; tone_preference added;
                   verification line omitted (Opus 5.5)
Refined English Prompt:
<role>You are a senior product growth strategist...</role>
...
Self-Review: 9/9 applicable gates passed (0 warnings, 3 N/A)
Final Output: Saved to ./onboarding-strategy-output.md
```

---

## Yapılandırma

`detect_model.py` tarafından okunan opsiyonel ortam değişkenleri. Ayarlandıklarında oturum tespitini geçersiz kılarlar.

| Değişken | Etki |
|---|---|
| `PROMPT_ARCHITECT_MODEL` | Hedef model, ID veya adıyla (örn. `claude-sonnet-5-5`, `gpt-6-astra`) |
| `PROMPT_ARCHITECT_EFFORT` | Hedefle birlikte raporlanan effort seviyesi (örn. `high`, `max`) |

---

## Nasıl Çalışır

| Aşama | Ne olur |
|---|---|
| 0 — Hedef Modeli Çözümle | Açık hedef → oturum tespiti → host varsayılanı. Yönlendirme matrisini, bir canon'u ve bir profili yükler |
| 1 — Analiz | Hedef, kısıtlar ve karmaşıklık skoru |
| 2 — Alan Sınıflandırma | 25 alanlık taksonomiden tek baskın alan |
| 3 — Pattern Seçimi | Görev ve hedefe göre süzülmüş, 14 pattern'in en küçük alt kümesi |
| 4 — Taslak | Kompakt, XML veya markdown iskelet, alan paketiyle zenginleştirilmiş |
| 5 — Öz-Denetim | Uygulanan kapılar, ardından bir revizyon turu |
| 6 — Yürütme | Yalnızca `prompt_and_execute` modunda |

Kaç model desteklenirse desteklensin her çalıştırmada üç dosya yüklenir, bağlam maliyeti sabit kalır.

### Model profilleri

| Profil | Kapsar | Belirleyici davranış |
|---|---|---|
| `opus-5-5` ★ | claude-opus-5-5 | Effort varsayılanı `medium`; thinking kapatılamaz; uygulamalar arasında hızlı harekete geçer, kapsamla; doğrulama satırı yok |
| `sonnet-5-5` | claude-sonnet-5-5 | Düşük effort'ta erken durup sorar, `xhigh`/`max`'ta fazlasını yapar; kod için gerçek kontrol ister |
| `haiku-5-5` | claude-haiku-5-5 | Effort'lu ilk Haiku; uzun ajan prompt'larında erken durur; sohbette kural kalıcılığı satırı gerekir |
| `fable-5-1` | claude-fable-5-1, claude-mythos-5-1 | Hafif iskelet, akıl yürütmeyi asla yazdırma, yalnızca eklemeli geçmiş, doğrulayıcı alt ajanlar |
| `gpt-sol` ★ | gpt-6.1-sol, gpt-6-sol, gpt-5.6-sol | Ana iş modeli; kısıtlar, done-when ve kontrol komutu |
| `gpt-astra` | gpt-6-astra | Öncü model; adım listesi yerine niyet |
| `gpt-terra` | gpt-6.1-terra, gpt-5.6-terra | Dengeli; işçi alt ajanlar için özet dönüş formatı |
| `gpt-luna` | gpt-6-luna, gpt-5.6-luna | Hızlı; tek dar hedef, kesin format, örnekler |
| `generic` | diğer her şey | Taşınabilir form, sağlayıcı ayarı yok |

Eski Claude profilleri (`opus-5`, `sonnet-5`, `opus-4-8`, `fable-5`) `references/models/legacy/` altındadır.

---

## Proje Yapısı

```
prompt-architect/
├── .claude-plugin/plugin.json        # Claude Code manifesti
├── .codex-plugin/plugin.json         # Codex manifesti
├── AGENTS.md / CLAUDE.md             # Ajanlar için depo rehberi
└── skills/prompt-architect/
    ├── SKILL.md                      # Giriş noktası + 7 aşamalı akış
    ├── references/
    │   ├── models/
    │   │   ├── _matrix.md            # Yönlendirme + matrisler (her zaman okunur)
    │   │   ├── _shared-canon.md      # Claude canon'u
    │   │   ├── _generic.md           # Ayarlanmamış taşınabilir form
    │   │   ├── {opus-5-5,sonnet-5-5,haiku-5-5,fable-5-1}.md
    │   │   ├── legacy/               # Opus 5, Sonnet 5, Opus 4.8, Fable 5
    │   │   └── openai/               # OpenAI canon'u + Sol/Astra/Terra/Luna
    │   ├── claude-prompting-patterns.md
    │   ├── quality-gates.md          # 12 kapı, N/A kuralı
    │   ├── domain-taxonomy.md
    │   ├── mode-inference.md
    │   └── working-rules.md          # Genel kurallar, iki katmanda
    ├── assets/templates/             # xml, compact, markdown + 6 alan paketi
    └── scripts/
        ├── detect_model.py           # Host/model/effort → profil
        └── validate_prompt.py        # Kalite kapısı doğrulayıcı
```

---

## Sınırlamalar

- **Profiller kendini güncellemez.** Her biri köken bilgisi olarak bir `last_verified` tarihi (2026-11-02) taşır. Modeller değişince elle yeniden türet. Karşılığında çalışma anında ağ gerekmez. **Geçici çözüm:** bir profile güvenmeden önce `last_verified` tarihine bak ve yeni sürümleri `claude plugin marketplace update skill-hub` veya `codex plugin marketplace upgrade skill-hub` ile al.
- **Bazı ID'ler çıkarımdır.** `claude-opus-5-5` canlı bir oturumdan doğrulandı; Sonnet 5.5, Haiku 5.5 ve Fable/Mythos 5.1 ID'leri Anthropic'in adlandırma kalıbını izler. Profiller bu tür bilgileri doğrulanmamış olarak işaretler. **Geçici çözüm:** model ID'n farklıysa `--target-model` veya `PROMPT_ARCHITECT_MODEL` ile ver; her model ID'si kabul edilir.
- **OpenAI rehberliği Claude'unkinden incedir.** Katman davranışı Codex model kataloğundan ve belgelerinden gelir; GPT-6.1 için modele özel bir prompting rehberi yok. Doğrulanmamış noktalar etiketlidir. **Geçici çözüm:** `references/models/openai/` altındaki profillerin doğrulanmamış olarak etiketlediği noktaları kullanmadan önce kontrol et.
- **Tespit için Claude Code veya Codex gerekir.** Diğer ajanlar açık hedefi veya generic profili kullanır. **Geçici çözüm:** hedef modeli isteğinde adıyla söyle ya da `PROMPT_ARCHITECT_MODEL` ayarla.
- **Kapı kontrolleri sezgiseldir.** Regex ve yapı taraması; prompt'u okumanın yerini tutmaz. **Geçici çözüm:** rafine prompt'u kullanmadan önce oku; WARN veya FAIL alan kapılardan başla.

---

## Sorun Giderme

**Skill tetiklenmiyor** — eklentinin kurulu olduğunu kontrol et (`claude plugin list` veya `codex plugin list`) ve oturumu yeniden başlat.

**`detect_model.py` `"host": "unknown"` döndürüyor** — Claude Code ve Codex dışındasın ya da oturum ortam değişkenleri script'e geçmiyor. Hedef modeli adıyla söyle veya `PROMPT_ARCHITECT_MODEL` ayarla.

**v3'te geçen bir prompt şimdi kalıyor** — beklenen durum. v4, akıl yürütmeyi yazdırma talimatını tüm güncel Claude modellerinde kesin hata yapar, Codex hedefleri için Kapı 12'yi ekler ve Claude hedeflerinde markdown bölümlerini hatalı sayar. Ayrıntılar [CHANGELOG](CHANGELOG.md)'da.

---

## Katkıda Bulunma

- Sorular ve fikirler: [Discussions](https://github.com/sametbrr/prompt-architect/discussions)
- Hatalar: [issue takibi](https://github.com/sametbrr/prompt-architect/issues)
- Pull request'ler: önce [katkı rehberini](https://github.com/sametbrr/.github/blob/main/CONTRIBUTING.md) okuyun
- Güvenlik bildirimleri: herkese açık issue yerine [güvenlik politikasını](https://github.com/sametbrr/prompt-architect/security/policy) izleyin

---

## Lisans

MIT — bkz. [LICENSE](LICENSE).

---

<div align="center">

[Hata Bildir](https://github.com/sametbrr/prompt-architect/issues) · [Özellik İste](https://github.com/sametbrr/prompt-architect/issues)

</div>
