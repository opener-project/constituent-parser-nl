Feature: Using files as input and output
  In order to parse constituency
  Using a file as an input
  Using a file as an output

  Scenario Outline: Extract opinions from KAF
    Given the fixture file "<input_file>"
    And I put them through the kernel
    Then the output should match the fixture "<output_file>"
  Examples:
    | input_file            | output_file      |
    | input.kaf             | output.kaf       |
    | file1.in.kaf          | file1.out.kaf    |
    | file2.in.kaf          | file2.out.kaf    |
