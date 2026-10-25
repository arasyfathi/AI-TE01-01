#ifndef forward_chain_h
#define forward_chain_h

#include <vector>
#include <string>
#include <utility>

class ForwardChain {
  
    public:
    
    std::vector<std::string> clause_variable_list = {
        "Tekanan darah tinggi dan perkembangan penyakit",
        "Penumpukan cairan tubuh",
        "Peradangan / Inflamasi",
        "Sirkulasi darah buruk",
        "Penyempitan pembuluh darah dan nyeri dada",
        "Kadar kolesterol tinggi",
        "Pembekuan / Gumpalan darah",
        "Peningkatan denyut jantung abnormal",
        "Penyumbatan pembuluh darah"
    };
    
    std::vector<std::string> treatment_list = {
        "OBAT ACE INHIBITOR / ARB BLOCKERS",
        "OBAT DIURETIK / ANTAGONIS ALDOSTERON",
        "KORTIKOSTEROID",
        "OBAT ACE INHIBITOR / ANGIOTENSIN II RECEPTOR BLOCKERS",
        "NITRAT",
        "STATIN (PENURUN KOLESTEROL)",
        "MANUVER VAGAL",
        "OBAT PENCEGAH PENGGUMPALAN DARAH (CLOPIDOGREL, TICAGRELOR) / ASPIRIN",
        "OBAT ANTI-ARITMIA",
        "NITRAT / OPERASI BEDAH JANTUNG TERBUKA"
    };
    
    std::vector<std::string> diagnosis_list = {
        "Gagal Jantung (Heart Failure)",
        "Kardiomiopati (Cardiomyopathy)",
        "Angina Pectoris (Angina)",
        "Penyakit Jantung Koroner (Coronary Artery Disease)",
        "Takikardia (Tachycardia)",
        "Takikardia Ventrikel (Ventricular Tachycardia)"
    };
    
    std::vector<std::pair<std::string, std::string>> variable_initialized_list = variable_initializer(clause_variable_list);
    
    std::vector<std::pair<std::string, std::string>> variable_initializer(std::vector<std::string> variable_list){
        std::vector< std::pair<std::string, std::string> > temp_var_initializer;
        for ( std::string variable : variable_list){
            std::pair<std::string, std::string> temp_pair = std::make_pair(variable, "");
            temp_var_initializer.push_back(temp_pair);
        }
        return temp_var_initializer;
    }
    
    std::vector< std::pair< int, std::vector<int>> > diagnosis_ailment = {
        {0, {0,1}}, {1, {2, 3}}, {2, {4, 5, 6}}, {3, {0,6}}, {4, {6,7}}, {7, {7,8}}
    };
    
    std::vector < std::vector<std::string> > ailment_condition = {
        {"TINGGI", "MENUMPUK"},
        {"INFLAMASI", "BERKURANG"},
        {"MENYEMPIT", "MENINGKAT", "BEKU"},
        {"TINGGI", "BEKU"},
        {"MENINGKAT", "BEKU"},
        {"MENINGKAT", "TERSUMBAT"}
    };
    
    std::vector<std::pair< std::vector<std::string>, std::string > > ailment_condition_treatment = {
        {{clause_variable_list[0], "TINGGI"}, "OBAT ACE INHIBITOR / ARB BLOCKERS"},
        {{clause_variable_list[1], "MENUMPUK"}, "OBAT DIURETIK / ANTAGONIS ALDOSTERON"},
        {{clause_variable_list[2], "INFLAMASI"}, "KORTIKOSTEROID"},
        {{clause_variable_list[3], "BERKURANG"}, "OBAT ACE INHIBITOR / ANGIOTENSIN II RECEPTOR BLOCKERS"},
        {{clause_variable_list[4], "MENYEMPIT"}, "NITRAT"},
        {{clause_variable_list[5], "MENINGKAT"}, "STATIN (PENURUN KOLESTEROL)"},
        {{clause_variable_list[6], "BEKU"}, "OBAT PENCEGAH PENGGUMPALAN DARAH (CLOPIDOGREL, TICAGRELOR) / ASPIRIN"},
        {{clause_variable_list[7], "MENINGKAT"}, "MANUVER VAGAL"}
    };
    
};

#endif /* forward_chain_h */
