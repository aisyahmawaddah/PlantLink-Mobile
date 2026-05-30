import 'package:flutter/material.dart';

class LocationDropdown extends StatefulWidget {
  final Function(String state, String? district)? onLocationSelected;
  final String? initialState;
  final String? initialDistrict;

  const LocationDropdown({
    super.key,
    this.onLocationSelected,
    this.initialState,
    this.initialDistrict,
  });

  @override
  State<LocationDropdown> createState() => _LocationDropdownState();
}

class _LocationDropdownState extends State<LocationDropdown> {
  final List<String> states = [
    "Johor", "Kedah", "Kelantan", "Melaka", "Negeri Sembilan",
    "Pahang", "Perak", "Perlis", "Pulau Pinang", "Sarawak",
    "Selangor", "Terengganu", "Kuala Lumpur", "Labuan", "Sabah", "Putrajaya"
  ];

  final Map<String, List<String>> districts = {
    "Johor": ["Johor Bahru","Tebrau","Pasir Gudang","Bukit Indah","Skudai","Kluang","Batu Pahat","Muar","Ulu Tiram","Senai","Segamat","Kulai","Kota Tinggi","Pontian Kechil","Tangkak","Bukit Bakri","Yong Peng","Pekan Nenas","Labis","Mersing","Simpang Renggam","Parit Raja","Kelapa Sawit","Buloh Kasap","Chaah"],
    "Kedah": ["Sungai Petani","Alor Setar","Kulim","Jitra / Kubang Pasu","Baling","Pendang","Langkawi","Yan","Sik","Kuala Nerang","Pokok Sena","Bandar Baharu"],
    "Kelantan": ["Kota Bharu","Pangkal Kalong","Tanah Merah","Peringat","Wakaf Baru","Kadok","Pasir Mas","Gua Musang","Kuala Krai","Tumpat"],
    "Melaka": ["Bandaraya Melaka","Bukit Baru","Ayer Keroh","Klebang","Masjid Tanah","Sungai Udang","Batu Berendam","Alor Gajah","Bukit Rambai","Ayer Molek","Bemban","Kuala Sungai Baru","Pulau Sebang","Jasin"],
    "Negeri Sembilan": ["Seremban","Port Dickson","Nilai","Bahau","Tampin","Kuala Pilah"],
    "Pahang": ["Kuantan","Temerloh","Bentong","Mentakab","Raub","Jerantut","Pekan","Kuala Lipis","Bandar Jengka","Bukit Tinggi"],
    "Perak": ["Ipoh","Taiping","Sitiawan","Simpang Empat","Teluk Intan","Batu Gajah","Lumut","Kampung Koh","Kuala Kangsar","Sungai Siput Utara","Tapah","Bidor","Parit Buntar","Ayer Tawar","Bagan Serai","Tanjung Malim","Lawan Kuda Baharu","Pantai Remis","Kampar"],
    "Perlis": ["Kangar","Kuala Perlis"],
    "Pulau Pinang": ["Bukit Mertajam","Georgetown","Sungai Ara","Gelugor","Ayer Itam","Butterworth","Perai","Nibong Tebal","Permatang Kucing","Tanjung Tokong","Kepala Batas","Tanjung Bungah","Juru"],
    "Sabah": ["Kota Kinabalu","Sandakan","Tawau","Lahad Datu","Keningau","Putatan","Donggongon","Semporna","Kudat","Kunak","Papar","Ranau","Beaufort","Kinarut","Kota Belud"],
    "Sarawak": ["Kuching","Miri","Sibu","Bintulu","Limbang","Sarikei","Sri Aman","Kapit","Batu Delapan Bazaar","Kota Samarahan"],
    "Selangor": ["Subang Jaya","Klang","Ampang Jaya","Shah Alam","Petaling Jaya","Cheras","Kajang","Selayang Baru","Rawang","Taman Greenwood","Semenyih","Banting","Balakong","Gombak Setia","Kuala Selangor","Serendah","Bukit Beruntung","Pengkalan Kundang","Jenjarom","Sungai Besar","Batu Arang","Tanjung Sepat","Kuang","Kuala Kubu Baharu","Batang Berjuntai","Bandar Baru Salak Tinggi","Sekinchan","Sabak","Tanjung Karang","Beranang","Sungai Pelek","Sepang"],
    "Terengganu": ["Kuala Terengganu","Chukai","Dungun","Kerteh","Kuala Berang","Marang","Paka","Jerteh"],
    "Kuala Lumpur": ["Chow Kit","Bangsar","Cheras","Kepong","Setapak","Wangsa Maju","Bukit Jalil","Damansara","Titiwangsa","Brickfields","Mont Kiara"],
    "Labuan": ["Labuan Town","Rancha-Rancha","Layang-Layang","Membedai"],
    "Putrajaya": ["Putrajaya"],
  };

  String? selectedState;
  String? selectedDistrict;

  bool _isValidState(String? state) {
    return state != null && states.contains(state);
  }

  bool _isValidDistrict(String? state, String? district) {
    return state != null &&
        district != null &&
        districts[state]?.contains(district) == true;
  }

  @override
  void initState() {
    super.initState();

    if (_isValidState(widget.initialState)) {
      selectedState = widget.initialState;
      selectedDistrict = _isValidDistrict(widget.initialState, widget.initialDistrict)
          ? widget.initialDistrict
          : null;
    } else {
      // Old data: search all districts to find matching state
      final searchTerm = widget.initialDistrict ?? widget.initialState;
      if (searchTerm != null && searchTerm.isNotEmpty) {
        for (final entry in districts.entries) {
          if (entry.value.contains(searchTerm)) {
            selectedState = entry.key;
            selectedDistrict = searchTerm;
            break;
          }
        }
      }
      if (selectedState == null &&
          widget.initialState != null &&
          widget.initialState!.isNotEmpty) {
        for (final entry in districts.entries) {
          if (entry.value.contains(widget.initialState!)) {
            selectedState = entry.key;
            selectedDistrict = widget.initialState;
            break;
          }
        }
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        DropdownButton<String>(
          value: selectedState,
          hint: const Text("Select State"),
          onChanged: (String? newState) {
            setState(() {
              selectedState = newState;
              selectedDistrict = null;
            });
            widget.onLocationSelected?.call(selectedState!, null);
          },
          items: states.map((state) {
            return DropdownMenuItem<String>(
              value: state,
              child: Text(state),
            );
          }).toList(),
        ),
        if (selectedState != null && districts[selectedState] != null)
          DropdownButton<String>(
            value: selectedDistrict,
            hint: const Text("Select District"),
            onChanged: (String? newDistrict) {
              setState(() {
                selectedDistrict = newDistrict;
              });
              widget.onLocationSelected?.call(selectedState!, selectedDistrict);
            },
            items: districts[selectedState]!.map((district) {
              return DropdownMenuItem<String>(
                value: district,
                child: Text(district),
              );
            }).toList(),
          ),
      ],
    );
  }
}