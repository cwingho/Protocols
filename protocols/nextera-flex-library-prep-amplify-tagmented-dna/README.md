# Nextera DNA Flex NGS Library Prep: Amplify Tagmented DNA

### Author
[Opentrons](https://opentrons.com/)



## Categories
* NGS Library Prep
	* Nextera DNA Flex Library Prep


## Description
This protocol performs the 'Amplify Tagmented DNA' section of the [Nextera DNA Flex Library Prep protocol](https://www.illumina.com/products/by-type/sequencing-kits/library-prep-kits/nextera-dna-flex.html).

Links:
* [Cherrypick Samples](./nextera-flex-library-prep-cherrypick-samples)
* [Tagment DNA](./nextera-flex-library-prep-tagment-dna)
* [Post Tagmentation Cleanup](./nextera-flex-library-prep-post-tag-cleanup)
* [Amplify Tagmented DNA](./nextera-flex-library-prep-amplify-tagmented-dna)
* [Cleanup Libraries](./nextera-flex-library-prep-cleanup-libraries)

---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

* [Opentrons magnetic module](https://shop.opentrons.com/collections/hardware-modules/products/magdeck)
* [Bio-Rad Hard Shell 96-well low profile PCR plate 200ul #hsp9601](bio-rad.com/en-us/sku/hsp9601-hard-shell-96-well-pcr-plates-low-profile-thin-wall-skirted-white-clear?ID=hsp9601)
* [Agilent single-channel reservoir 290ml #201252-100](https://www.agilent.com/store/en_US/Prod-201252-100/201252-100)
* [Opentrons 4-in-1 tuberack with 2ml Eppendorf tubes](https://shop.opentrons.com/collections/racks-and-adapters/products/tube-rack-set-1)
* [P50 Single-channel electronic pipette](https://shop.opentrons.com/collections/ot-2-pipettes)
* [P300 Single/multi-channel electronic pipette](https://shop.opentrons.com/collections/ot-2-pipettes)
* [300ul Opentrons tipracks](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-300ul-tips)

---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

Preprogram the thermocycler according to the BLT PCR program parameters described in the kit manual.

4x6 aluminum block tuberack (slot 4, mounted on temperature module)
* A1-C1: mastermix 1.5ml snapcap tubes (loaded empty, 1 tube needed per 32 samples)
* A2-D2: EPM in 0.5ml false-bottom tubes (1 tube needed per 24 samples)
* A3-B3: nuclease-free water in 1.5ml snapcap tubes (1 tube needed per 48 samples)

### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process
1. Input the mount sides for your P50 and P300 pipettes and the number of samples to process.
2. Download your protocol.
3. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
4. Set up your deck according to the deck map.
5. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
6. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).
