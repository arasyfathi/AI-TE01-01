#include <stdio.h>
#include <vector>
#include <stack>
#include <map>
#include <unordered_map>
#include <iostream>
#include "knowledge_base-Project1-A05071238.h"
#include "forward_rules-Project1-A05071238.h"

/*
Indeks Diagnosis (Goal/Tujuan):
0: Gagal Jantung (Heart Failure)
1: Kardiomiopati (Cardiomyopathy)
2: Angina Pectoris (Angina)
3: Penyakit Jantung Koroner (Coronary Artery Disease)
4: Takikardia (Tachycardia)
5: Takikardia Ventrikel (Ventricular Tachycardia)
*/

class Rules{

public:
  Rules() {};

private:
    std::string final_diagnosis = "";

std::vector<int>rule_number = {10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200, 210, 220, 230, 240, 250, 260, 270, 280, 290, 300, 310, 320, 330, 340, 350, 360};

std::vector<int> diagnosis_index = {0,0,0,1,1,5,5,2,2,5,1,1,1,2,2,2,5,5,2,0,0,2,2,1,0,0,2,0,2,0,3,3,3,3,2,0};

std::vector<std::vector<int>>symptoms_combination = {
  {0,1,6},
  {0,12},
  {0,20},
  {0,10},
  {0,11},
  {0,18},
  {0,19},
  {1,2,6},
  {1,2,7},
  {1,2,8},
  {1,2,9},
  {1,10},
  {1,11},
  {1,13},
  {1,14},
  {1,15},
  {1,18},
  {1,19},
  {1,3,7},
  {1,3,8},
  {1,20},
  {1,5,6},
  {1,5,7},
  {1,5,9},
  {1,12},
  {1,6,9},
  {1,6,7},
  {1,6,8},
  {1,7},
  {1,8,9},
  {0,16},
  {0,17},
  {0,7},
  {0,8,9},
  {1,4,7},
  {1,4,9}
};

std::map< int, std::vector<int> > rule_symptoms = initialize_rule_symptoms(rule_number, symptoms_combination);
std::vector<std::pair<int,std::string>>conclusion_list = initialize_conclusion_list(36);
std::vector<std::pair<int,std::string>>visited_conclusion_list;
std::stack<std::pair<int, int>>conclusion_stack = initialize_stack();

std::stack<std::pair<int, int>> initialize_stack () {
  std::stack<std::pair<int, int>>conclusion_stack;
  conclusion_stack.push(std::make_pair(10,0));
  return conclusion_stack;
}

std::vector< std::pair<int,std::string> >initialize_conclusion_list(int numRules){
  std::vector<std::pair<int, std::string > > rules_conclusions;
  for ( int i = 1; i <= numRules; i++){
    std::pair< int, std::string> tempPair;
    tempPair = std::make_pair(i, "diagnosis");
    rules_conclusions.push_back(tempPair);
  }
  return rules_conclusions;
}

std::map< int, std::vector<int> > initialize_rule_symptoms( std::vector<int> rules, std::vector<std::vector<int>> symptoms){
    std::map< int, std::vector< int> > rule_symptoms;
    if ( rules.size() != symptoms.size()){
        printf("Rules and symptoms size mismatch. Recheck data.\n");
        return rule_symptoms;
    }
    for ( int i = 0; i < rules.size(); i++){
        rule_symptoms[rules[i]] = symptoms[i];
    }
    return rule_symptoms;
}

Knowledge_base current_knowledge = Knowledge_base();

public:

std::pair<int, int> check_conclusion_stack(){
  if (conclusion_stack.empty()){
    conclusion_stack.push( std::make_pair(10, 0));
  }
  return conclusion_stack.top();
}

void start_iteration(){
    std::string response;
    int response_value;

    std::pair<int, int> rule_to_process = check_conclusion_stack();
    int variable_index = rule_to_process.second;

    while ( (response != "Y") && (response != "N") && (response != "y") && (response != "n") && (response != "T") && (response != "t") ){
        std::string condition = current_knowledge.variables_list[variable_index];
        printf("Apakah pasien mengalami: %s?\n[Ketik Y untuk Ya / T untuk Tidak]: ", condition.c_str());
        std::cin >> response;
    }
    
    if ( response == "Y" || response == "y"){
      response_value = 1;
    } else {
      response_value = 0;
    }
    
    updateResponse(response_value, variable_index);
}

void updateResponse( int variable_value, int variable_position){
    current_knowledge.variable_initialized[current_knowledge.variables_list[variable_position]] = variable_value;
    std::pair<int, int> rule_to_process = check_conclusion_stack();
    int rule_num_to_process = rule_to_process.first;
    processResponse(rule_num_to_process);
}

void processResponse( int rule_num_to_process){
    int next_rule = -1;
    std::vector<int>symptoms_for_rule = rule_symptoms[rule_num_to_process];

    for ( int symptom : symptoms_for_rule){
         if (current_knowledge.variable_initialized[current_knowledge.variables_list[symptom]] == 0){
              visited_conclusion_list.push_back({rule_num_to_process, "diagnosis"});
              conclusion_stack.pop();
              next_rule = ( rule_num_to_process + 10 );
             
             if ( next_rule > rule_number[rule_number.size() - 1] ){
                    printf("\n[!] Diagnosis tidak dapat ditentukan dengan gejala yang dimasukkan.\nSilakan rujuk pasien ke Dokter Spesialis Jantung (Sp.JP) untuk pemeriksaan lebih mendalam.\n");
                    endProgram();
             } 
              
             std::vector<int> next_set_of_symptom = rule_symptoms[next_rule];
             conclusion_stack.push({next_rule, next_set_of_symptom[0]});
             processResponse(next_rule);
        }
        else if ( current_knowledge.variable_initialized[current_knowledge.variables_list[symptom]] == -1) {
            next_rule = rule_num_to_process;
             conclusion_stack.pop();
             conclusion_stack.push({next_rule, symptom});
             start_iteration();
        }
    }
    
    if ( next_rule == -1){
        printf("\n=======================================================================\n");
        printf("                       HASIL DIAGNOSIS SISTEM PAKAR                    \n");
        printf("=======================================================================\n\n");
        printf("Pasien teridentifikasi memiliki gejala-gejala berikut:\n");
        
        for ( auto each_symptom : rule_symptoms[rule_num_to_process]){
            std::string symptom_description = current_knowledge.variables_list[each_symptom];
            printf("  * %s\n", symptom_description.c_str());
        }
        
        final_diagnosis = current_knowledge.conclusions[diagnosis_index[(rule_num_to_process/ 10) - 1]];
        
        printf("\n>>> KESIMPULAN DIAGNOSIS:\n");
        printf("    Pasien kemungkinan menderita: %s\n", final_diagnosis.c_str());
        printf("    (Disarankan melakukan tes medis lanjutan untuk konfirmasi kondisi).\n\n");
        printf("-----------------------------------------------------------------------\n");
        printf("            REKOMENDASI PENGOBATAN & TINDAKAN KLINIS (FORWARD CHAIN)   \n");
        printf("-----------------------------------------------------------------------\n");
        endProgram();
    }
}
    
void endProgram(){
    Forward_Rules treatment = Forward_Rules( getDiagnosis());
    if ( this-> getDiagnosis() == ""){
        treatment.end_program();
    } else {
        treatment.initialize_forward_rule();
    }
}
    
std::string getDiagnosis(){
    return this->final_diagnosis;
}

};
