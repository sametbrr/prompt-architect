[![GitHub release](https://img.shields.io/github/v/release/sametbrr/prompt-architect?display_name=tag&sort=semver)](https://github.com/sametbrr/prompt-architect/releases/latest)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Agent Skills](https://img.shields.io/badge/agentskills.io-compatible-blue)](https://agentskills.io)

# Prompt Architect

Ham bir fikri domain sınıflandırması, kalite incelemesi ve pattern analizi yaparak uzman seviye bir prompt'a dönüştüren Agent Skill. Türkçe ve İngilizce girdi destekler.

> 🇬🇧 For English see [README.md](README.md)

---

## Hızlı Başlangıç

```bash
git clone https://github.com/sametbrr/prompt-architect.git ~/.claude/skills/prompt-architect
```

Claude Code oturumunuzu yeniden başlatın, ardından doğal dille tetikleyin:

```
> "Bunu uzman bir prompt'a çevir: B2B SaaS için onboarding stratejisi oluştur"
```

---

## Özellikler

`"onboarding stratejisi oluştur"` veya `"X için API tasarla"` gibi belirsiz bir giriş verildiğinde skill:

1. **Analiz eder** — amaç, kısıtlar, karmaşıklık skoru (basit / orta / karmaşık).
2. **Domain sınıflandırır** — TR + EN sinyal kelimeleriyle 25 domainlik bir sınıflandırma yapar.
3. **3–6 prompting pattern seçer** — 9 UI-uyumlu pattern arasından göreve uygun olanları belirler.
4. **Taslak yazar** — compact bullet iskelet veya tam XML iskeletiyle İngilizce prompt üretir.
5. **Kalite incelemesi yapar** — 8 kalite geçidine karşı kendi kendini denetler.
6. **Çalıştırır** — sadece kullanıcı isterse prompt'u çalıştırır ve çıktıyı diske kaydeder.

Üretilen prompt gövdesi her zaman İngilizce yazılır; bölüm etiketleri kullanıcının giriş diline göre şekillenir.

---

## Gereksinimler

- Python 3.10+ (opsiyonel doğrulayıcı scripti için — pip kurulumu gerekmez)
- Claude Code veya herhangi bir [agentskills.io](https://agentskills.io) uyumlu agent

---

## Kurulum

```bash
git clone https://github.com/sametbrr/prompt-architect.git ~/.claude/skills/prompt-architect
```

Claude Code, `~/.claude/skills/` altındaki skill'leri otomatik keşfeder. Klonladıktan sonra oturumunuzu yeniden başlatın.

---

## Kullanım

### Modlar

| İstediğiniz… | Söyleyin… | Mod |
|---|---|---|
| Sadece prompt | `sadece prompt`, `çalıştırma`, `just the prompt` | `prompt_only` (varsayılan) |
| Prompt + çıktı | `çalıştır`, `execute it`, `üret de` | `prompt_and_execute` |

### Örnek

**Girdi:**
> B2B SaaS için onboarding stratejisi oluştur ve çalıştır

**Çıktı (özet):**

```
Tespit Edilen Domain: Ürün Büyüme Stratejisi
Karmaşıklık: orta
Seçilen Patternlar: Role, XML Structuring, Positive Guidance, CoT, Output Framing

Rafine İngilizce Prompt:
<role>You are a senior product growth strategist...</role>
<task>Design a B2B SaaS onboarding strategy...</task>
...

Kalite İncelemesi: 8/8 geçit başarılı
Nihai Çıktı: ./onboarding-strategy-output.md dosyasına kaydedildi
```

---

## Depo Yapısı

```
prompt-architect/
├── SKILL.md                          # Skill giriş noktası + 6 aşamalı iş akışı
├── references/
│   ├── claude-prompting-patterns.md  # 9 UI-uyumlu pattern
│   ├── quality-gates.md              # 8 kalite geçidi + örnek olay
│   ├── domain-taxonomy.md            # 25 domain, TR + EN sinyal kelimeleri
│   ├── mode-inference.md             # prompt_only vs prompt_and_execute
│   └── claude-md-rules.md            # İkili katmanda uygulanan yazım kuralları
├── assets/templates/
│   ├── refined-prompt-xml.tmpl       # Tam XML iskeleti (karmaşık görevler için varsayılan)
│   ├── refined-prompt-compact.tmpl   # Bullet iskeleti (basit görevler)
│   └── domain-*.tmpl                 # 6 domain paketi
└── scripts/
    └── validate_prompt.py            # İsteğe bağlı 8-geçit doğrulayıcı (stdlib)
```

---

## Temel Tasarım Kararları

- **Claude için özel tasarım.** Claude Code, claude.ai ve Agent Skills uyumlu istemciler için geliştirilmiş olup Anthropic'in resmi prompt mühendisliği yaklaşımlarını uçtan uca uygular. Üretilen prompt çıktıları diğer LLM'lerle de kullanılabilir.
- **Yalnızca UI-uyumlu.** API düzeyinde erişim gerektiren patternlar (assistant prefill, `thinking`, `stop_sequences`, `tool_choice`) kapsam dışıdır. Her şey normal bir sohbet penceresinde çalışır.
- **İkidilli girdi, İngilizce gövde.** Skill Türkçe veya İngilizce girdi kabul eder; üretilen prompt gövdesi her zaman İngilizce olur.
- **Minimum pattern.** Skill görev başına 3–6 pattern seçer, 9'unu birden kullanmaz. Sadelik önceliklidir.
- **Gereksiz soru sormaz.** Girdi gerçekten kullanılamaz durumdaysa soru sorulur. Aksi halde varsayımlar belirtilerek devam edilir.
- **Dosya çıktısı disiplini.** Execute modunda yapılandırılmış çıktılar (>~50 satır) diske kaydedilir; ekrana yalnızca özet yazdırılır.

---

## Doğrulayıcı

```bash
python3 scripts/validate_prompt.py --stdin < taslak-prompt.txt
python3 scripts/validate_prompt.py --self-test
```

Saf stdlib, Python 3.10+.

---

## Uyumluluk

| Araç | Skills yolu | Notlar |
|---|---|---|
| Claude Code | `~/.claude/skills/` veya `.claude/skills/` | Global veya proje düzeyinde |
| GitHub Copilot (VS Code) | `.vscode/skills/` | Agent modu gerekli |
| OpenAI Codex | `~/.codex/skills/` | Aynı SKILL.md formatı |
| Cursor | `.cursor/skills/` | Proje düzeyinde |
| Gemini CLI | `~/.gemini/skills/` | |

---

## Lisans

MIT — bkz. [LICENSE](LICENSE).
