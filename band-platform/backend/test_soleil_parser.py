#!/usr/bin/env python3
"""
Test script for the new SOLEIL Content Parser.
This demonstrates how your existing naming conventions are now properly parsed.
"""

from modules.content.services.soleil_content_parser import parse_filename, SOLEILContentParser

def test_filename_parsing():
    """Test the SOLEIL content parser with various filename formats."""
    
    # Test filenames from your existing system
    test_filenames = [
        "Take Five - Bb Trumpet.pdf",
        "All of Me - Bb.pdf", 
        "Spain - Chick Corea - Eb.pdf",
        "Summertime - Rhythm - C.pdf",
        "Take Five - Eb - Medium Swing.pdf",
        "All of Me - Jazz Standard - Duke Ellington - Bb.pdf",
        "SomeRandomFile.txt",
        "All of Me - Reference.mp3",
        "Gimme Gimme SP (with Cues).mp3",
        "Stand By Me - SPL (Instrumental).mp3",
        "Best Of My Love_Lil Boo Thang.pdf",
        "Toxic_Tenor.pdf",
        "t_s My Life - Bari.pdf",
        "Best Of My Love_Lil Boo Thang.pdf"
    ]
    
    print("🎵 Testing SOLEIL Content Parser")
    print("=" * 60)
    
    parser = SOLEILContentParser()
    
    for filename in test_filenames:
        try:
            result = parser.parse_filename(filename)
            print(f"\n📁 {filename}")
            print(f"   🎵 Title: {result.song_title}")
            print(f"   🎼 Key: {result.key}")
            print(f"   📄 Type: {result.chart_type}")
            print(f"   🎯 Transposition: {result.transposition}")
            print(f"   🏷️  Suffix: {result.suffix}")
            print(f"   🎵 Tempo: {result.tempo}")
            print(f"   📊 Format: {result.metadata.get('original_format', 'unknown')}")
            
        except Exception as e:
            print(f"\n❌ Error parsing '{filename}': {e}")
    
    print(f"\n📊 Parser Statistics:")
    stats = parser.get_stats()
    for key, value in stats.items():
        if isinstance(value, dict):
            print(f"   {key}:")
            for subkey, subvalue in value.items():
                print(f"     {subkey}: {subvalue}")
        else:
            print(f"   {key}: {value}")

def test_instrument_mapping():
    """Test the instrument to transposition mapping."""
    
    print(f"\n🎺 Testing Instrument to Transposition Mapping")
    print("=" * 60)
    
    from modules.content.services.soleil_content_parser import get_instrument_key, is_chart_accessible_by_user
    
    test_instruments = [
        "tenor", "alto_sax", "trumpet", "trombone", 
        "piano", "guitar", "bass", "vocals"
    ]
    
    for instrument in test_instruments:
        key = get_instrument_key(instrument)
        print(f"   {instrument:12} → {key}")
    
    print(f"\n🎯 Testing Chart Access Control")
    print("-" * 40)
    
    # Test if a Bb chart is accessible by different instruments
    chart_key = "Bb"
    test_user_instruments = [
        ["tenor", "trumpet"],      # Should access Bb charts
        ["alto_sax", "piano"],     # Should access Bb charts (alto is Eb, piano is Concert)
        ["trombone", "bass"],      # Should NOT access Bb charts (both are Concert)
    ]
    
    for i, user_instruments in enumerate(test_user_instruments, 1):
        can_access = is_chart_accessible_by_user(chart_key, user_instruments)
        print(f"   User {i} ({', '.join(user_instruments)}): {'✅ Can access' if can_access else '❌ Cannot access'} Bb charts")

if __name__ == "__main__":
    test_filename_parsing()
    test_instrument_mapping()
    print(f"\n🎉 SOLEIL Content Parser test completed!")
