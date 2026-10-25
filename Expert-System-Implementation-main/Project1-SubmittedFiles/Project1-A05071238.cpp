/*
  Implementasi Sistem Pakar (Expert System) menggunakan Backward Chaining dan Forward Chaining
  untuk diagnosis penyakit kardiovaskular (jantung) serta rekomendasi pengobatan.
  
  Mata Kuliah: Kecerdasan Buatan (AI-TE01) - S1 Teknik Elektro
*/

#include <iostream>
#include "rules-Project1-A05071238.h"

int main(){
  std::cout << "=======================================================================\n";
  std::cout << "  SISTEM PAKAR: DIAGNOSIS & REKOMENDASI PENGOBATAN PENYAKIT JANTUNG    \n";
  std::cout << "=======================================================================\n\n";
  std::cout << "Silakan jawab pertanyaan gejala berikut untuk mendiagnosis pasien.\n\n";

  Rules heart_disease_diagnosis = Rules();
  heart_disease_diagnosis.start_iteration();

  return 0;
}
