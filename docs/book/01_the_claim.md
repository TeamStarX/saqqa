## 1 · The claim

### The sentence

> A water delivery is paid for on the word of the person being paid.

Everything Saqqa does follows from that sentence, so be able to defend it before anything else.

A tanker arrives at a camp, a clinic, a hotel, a construction site. Someone signs a form saying ten cubic metres were delivered. The signature releases the money. Nobody measured the water: there is no meter on the truck and none on the tank. The number on the form is the number the driver said.

This is not a hypothetical. UNHCR's water-trucking log book, form F-306, records hand-written GPS coordinates and a pen signature from a delivery-point representative, and says on its face that it "will be used as part of the payment justification process to the contractor." Copies are posted weekly. We have the form; it is on slide 3 of the deck.

### Why it matters now

Drought has made the water truck the actual utility for millions of people across the region, and nobody meters it.

- **Jordan.** Tanker markets generate US$176 million a year, 8% more than all of Jordan's public water suppliers combined; about 91% of tanker water is obtained from illegal sources; tanker water costs about 4.8 times piped water; unregulated sales exceed licences 10.7-fold. Household reliance is projected to grow 2.6-fold by 2050. (Klassert et al., *Nature Sustainability* 6:1406, 2023, open access. We read the paper, not a summary of it.)
- **Iraq.** The driest year since 1933. Basra's 4.5 million people are on daily deliveries (UNICEF). This is why the demo site is Camp Al-Zubair, Basra.
- **Yemen.** 215,000 displaced people across 97 sites depend on trucked water as "the only reliable source of safe drinking water"; the WASH sector received $37.4 million of the $176.9 million it needed in 2025 (Bond, 11 August 2026). Austerity is the argument for verification, not against it: a funder at a fifth of need cannot afford to pay for water that did not arrive.

### The one cause, and the four frauds it permits

The only record of a delivery is created by the party being paid for it. Four frauds follow, and they are not the obvious ones. A truck that never turns up is reported within the hour by a thirsty household. These survive because nobody who could report them has a reason to.

| Fraud | What happens | Why nobody catches it |
|---|---|---|
| Short-filling | The tanker arrives two-thirds full and is paid for a full load. | Nobody at the tank has a meter, so there is nothing to disagree with. |
| Diversion | The load is sold somewhere that pays better; the delivery is logged anyway. | Nobody records where the truck actually went. |
| Ghost trips | Trips are billed that never happened. | The log book is the only record the trip existed. |
| A bought signature | The delivery-point representative signs for a few dinars. | The signature is the payment trigger, so buying it is the whole attack. |

### What Saqqa does about it

Measure the water at the tank. Verify the trip with the mobile network. Let an agent decide what it is willing to believe, and pay for the litres it can account for, with the reasoning written down.

The payer (an aid agency, a municipality, a hotel) puts two SIMs into the contract as a condition of it. One sits in the tanker's cab. The other is in a level-and-turbidity sensor bolted to the payer's own tank. Nothing goes on the contractor's vehicle body except the cab SIM, and nothing is asked of any household. Every SIM Saqqa queries belongs to an organisation, so no person is located, messaged or asked to consent.

The line that a telecom person recognises, and the one to lead with in the room:

> The tank sensor is the meter. The network is the meter-reader nobody can bribe. The agent is the billing engine.

### The honest division of labour

Say this before anyone asks, because the sharp question in the room is "isn't the network just garnish on an IoT project?"

The network does not measure water, and we never say it does. The tank level alone proves water arrived. What only the network can add:

- **Attribution.** Which contractor's truck was in the zone when the level rose (Geofencing on the cab SIM).
- **Source.** The truck visited the contracted well, not an unlicensed one (the sequence of zones).
- **Sensor integrity.** The sensor SIM is still at its install point (Location Verification), reachable (Device Reachability), and not moved into another device (Device Swap). The network is the witness to the witness, and it is the one witness the contractor cannot tamper with.
- **Payee protection.** SIM Swap on the payee's number before money moves.

Any claim that the network measures water would be false, and the first engineer in the room would know it.

### Why the network and not a GPS tracker

Because resolution is the wrong axis. A tracker reports its own position, and anything that reports its own position can be made to lie; a tamper-evident seal stops a screwdriver, not a spoofed signal. Cell-level location is coarse, about two kilometres, and it is computed by infrastructure the contractor does not own and cannot reach. Two thousand metres you cannot forge beats five metres you report yourself, when you are the party being audited. And the hardware sits on the payer's tank, so the truck carries nothing to disable, swap or drive around with.

That is the whole design in one word: forgeability, not resolution. Chapter 6 says what this argument does not cover.

### What we are not claiming

- Not that the network locates anything to a house. Zone scale, about two kilometres, never a single tank inside a district.
- Not that fraud is impossible. The best attack we found (substituting dirty water inside the zone) is caught by a ten-dollar turbidity probe, not by the network; chapter 6.
- Not that an operator in the region sells these APIs commercially today. The location family is not yet live with a MENA operator; Phase 1 runs on Nokia's sandbox and says so on every screen.
- Not that the sensor is built. It is a model in Phase 1, hardware in Phase 3.
