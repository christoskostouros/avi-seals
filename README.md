# avi-seals — δημόσιος καθρέφτης των σφραγίδων του AI Visibility Index

Ο [AI Visibility Index](https://ai-visibility-index-livid.vercel.app/methodology) μετρά κάθε μέρα τι απαντούν τα AI
(ChatGPT, Gemini, AI Mode) σε πραγματικές ερωτήσεις καταναλωτών στην Ελλάδα, ανά κλάδο. Κάθε μέρα μέτρησης κλείνει με
μια **σφραγίδα** (SHA-256 πάνω στις απαντήσεις, το πλαίσιο ερωτήσεων και τον χάρτη του κλάδου). Κάθε πρωί στις 07:50
ώρα Ελλάδας, οι νέες σφραγίδες μπαίνουν σε μια λίστα και η λίστα παίρνει **χρονοσφραγίδα RFC 3161** από δύο
ανεξάρτητες υπηρεσίες (FreeTSA, DigiCert). Αυτή είναι η **άγκυρα** της ημέρας.

Αυτό το αποθετήριο είναι ένα αντίγραφο κάθε άγκυρας **έξω από τα χέρια μας**: ένα GitHub Action (στους servers του
GitHub, όχι σε δικό μας μηχάνημα) κατεβάζει κάθε μέρα στις 08:30 ώρα Ελλάδας ό,τι νέο δημοσιεύει η σελίδα
[/methodology/seals](https://ai-visibility-index-livid.vercel.app/methodology/seals) και το κάνει commit. Το ιστορικό
του git δείχνει **πότε** κατέβηκε το καθένα· η υπογραφή της υπηρεσίας δείχνει **πότε υπήρχε** η λίστα. Ό,τι μπήκε
δεν ξαναγράφεται ποτέ (append-only).

## Τι περιέχει

```
index.json                     το ευρετήριο όπως το σερβίρει η σελίδα (τελευταία λήψη)
anchors/<id>/list.txt          τα ακριβή bytes που πήραν χρονοσφραγίδα: «κωδικός μέρας μέτρησης, κενό, σφραγίδα», μία γραμμή ανά μέρα
anchors/<id>/freetsa.tst       η υπογραφή της FreeTSA (TimeStampToken, DER)
anchors/<id>/digicert.tst      η υπογραφή της DigiCert (TimeStampToken, DER)
anchors/<id>/meta.json         αναγνωριστικό, ώρα, πλήθος σφραγίδων, SHA-256 της λίστας, SHA-256 κάθε υπογραφής
scripts/mirror.py              ο καθρέφτης (Python, μόνο η βιβλιοθήκη της γλώσσας)
.github/workflows/mirror.yml   το καθημερινό Action
```

## Πώς το ελέγχει οποιοσδήποτε

Χρειάζεται μόνο το OpenSSL (υπάρχει έτοιμο σε Linux και macOS).

**1. Η λίστα είναι αυτή που υπογράφηκε.** Το αποτύπωμά της πρέπει να είναι ίδιο με το `list_sha256` του `meta.json`:

```bash
sha256sum anchors/<id>/list.txt
```

**2. Η υπογραφή της FreeTSA.** Πιστοποιητικά: [cacert.pem](https://freetsa.org/files/cacert.pem) και
[tsa.crt](https://freetsa.org/files/tsa.crt).

```bash
openssl ts -verify -data anchors/<id>/list.txt -in anchors/<id>/freetsa.tst -token_in \
  -CAfile cacert.pem -untrusted tsa.crt
```

**3. Η υπογραφή της DigiCert.** Πιστοποιητικό:
[DigiCertTrustedRootG4.crt](https://cacerts.digicert.com/DigiCertTrustedRootG4.crt), που μετατρέπεται σε PEM με την
πρώτη εντολή:

```bash
openssl x509 -inform DER -in DigiCertTrustedRootG4.crt -out DigiCertTrustedRootG4.pem
openssl ts -verify -data anchors/<id>/list.txt -in anchors/<id>/digicert.tst -token_in -CAfile DigiCertTrustedRootG4.pem
```

Και οι δύο απαντούν `Verification: OK`. Αν η λίστα αλλάξει έστω κατά έναν χαρακτήρα, απαντούν `Verification: FAILED`.
Για να δεις την ώρα της υπογραφής:

```bash
openssl ts -reply -in anchors/<id>/freetsa.tst -token_in -text
```

**4. Από τη σφραγίδα στα δεδομένα.** Στη σελίδα κάθε επιχείρησης (`/index/<domain>`) η γραμμή «Σφραγίδα μέτρησης»
δείχνει τα 12 πρώτα ψηφία της σφραγίδας της ημέρας· βρες τη γραμμή του `list.txt` που τα έχει μετά το κενό. Τι
μπαίνει στο αποτύπωμα και πώς ξαναϋπολογίζεται από τα αποθηκευμένα πεδία της μέρας:
[/methodology#seal](https://ai-visibility-index-livid.vercel.app/methodology#seal).

## Τι ΔΕΝ αποδεικνύει

Η χρονοσφραγίδα αποδεικνύει ότι **αυτή η λίστα υπήρχε εκείνη την ώρα** και δεν άλλαξε από τότε. Δεν αποδεικνύει ότι
οι μετρήσεις είναι σωστές — αυτό το κρίνει η [μεθοδολογία](https://ai-visibility-index-livid.vercel.app/methodology)
και τα ίδια τα αποθηκευμένα δεδομένα.

---

**English.** This repository is an independent, append-only mirror of the daily RFC 3161 timestamp anchors of the
AI Visibility Index (Greece). Each `anchors/<id>/` holds the exact `list.txt` that was timestamped (one line per
sealed measurement day: cohort id, space, SHA-256 seal) and the TimeStampTokens of FreeTSA and DigiCert. Verify with
the `openssl ts -verify … -token_in` commands above. A GitHub Action fetches new anchors daily at 05:30 UTC from
`/methodology/seals/index.json`; nothing already mirrored is ever rewritten.
