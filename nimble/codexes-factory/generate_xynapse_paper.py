  import sys
  sys.path.insert(0, 'src')
  from codexes.modules.imprints.academic_paper_integration import generate_paper_for_new_imprint

  print("🚀 Generating academic paper for xynapse_traces imprint...")
  result = generate_paper_for_new_imprint('xynapse_traces')

  if result and result.get('success'):
      print('✅ Paper generated successfully!')
      print(f'📁 Output directory: {result.get("output_directory")}')
      print(f'📄 Imprint: {result.get("imprint_name")}')
  else:
      error = result.get('error', 'Unknown error') if result else 'Generation failed'
      print(f'❌ Paper generation failed: {error}')
  EOF

exit()
