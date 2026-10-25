#ifndef forward_rules_h
#define forward_rules_h

#include <queue>
#include <iostream>
#include "forward_knowledge_base-Project1-A05071238.h"

class Forward_Rules {
    
public:
    std::string diagnosis;
    std::queue <std::pair <std::string, std::string> >variables_initialized_queue;
    ForwardChain chain_forward = ForwardChain();
    
    void initialize_ailment( int diagnosis_index) {
        for ( auto diagnosis_ailment_pair : chain_forward.diagnosis_ailment) {
            if ( diagnosis_index == diagnosis_ailment_pair.first){
                std::vector<int> ailments_index = diagnosis_ailment_pair.second;
                for ( auto ailment_number : ailments_index){
                    chain_forward.variable_initialized_list[ailment_number].second = chain_forward.ailment_condition[diagnosis_index][ailment_number];
                    variables_initialized_queue.push(chain_forward.variable_initialized_list[ailment_number]);
                }
            }
        }
        apply_forward_chain(variables_initialized_queue);
    }
    
    void apply_forward_chain(std::queue< std::pair<std::string, std::string > >variables_initialized_queue){
        while ( ! variables_initialized_queue.empty() ){
            std::pair< std::string, std::string> variable = variables_initialized_queue.front();
            variables_initialized_queue.pop();
            
            for ( auto ailment_condition_treat : chain_forward.ailment_condition_treatment){
                std::vector<std::string> ailment_condition = ailment_condition_treat.first;
                
                if ( variable.first == ailment_condition[0] ) {
                    std::string output_print = "\n- Kondisi Klinis Terkait : " + variable.first;
                    std::string treatment_print = "  -> Terapi / Rekomendasi : " + ailment_condition_treat.second;
                    
                    std::cout << output_print << std::endl;
                    std::cout << treatment_print << std::endl;
                }
            }
        }
    }
    
    int end_program() {
        std::cout << "\n=======================================================================\n";
        std::cout << "  Terima kasih telah menggunakan Sistem Pakar Diagnosis Jantung!\n";
        std::cout << "=======================================================================\n\n";
        system("pause"); exit(0);
    }
    
public:
    Forward_Rules( std::string diagnosis){
        this->diagnosis = diagnosis;
    };
    
    void initialize_forward_rule (){
        int diagnosis_index = 0;
        for ( int i = 0; i < chain_forward.diagnosis_list.size(); i++ ){
            if ( chain_forward.diagnosis_list[i] == this->diagnosis){
                diagnosis_index = i;
                break;
            }
        }
        initialize_ailment(diagnosis_index);
        end_program();
    }
};

#endif /* forward_rules_h */
