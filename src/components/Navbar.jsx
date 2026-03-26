import { useEffect, useState } from 'react';
import { Search, Bell, Menu } from 'lucide-react';

const Navbar = ({ onSearch, searchQuery, activeCategory, onCategoryChange }) => {
  const [isScrolled, setIsScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 0);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const categories = ['Home', 'TV Shows', 'Movies', 'New & Popular', 'My List'];

  return (
    <nav className={`fixed top-0 left-0 right-0 z-[200] flex items-center justify-between px-4 md:px-11 transition-all duration-300 ${isScrolled ? 'bg-[#090910]/95 backdrop-blur-md py-3 border-b border-white/5 shadow-2xl' : 'bg-gradient-to-b from-[#090910] to-transparent py-5'}`}>
      <div 
        className="font-['Bebas_Neue'] text-2xl md:text-3xl tracking-[6px] text-[#e8192c] cursor-pointer hover:opacity-80 transition-opacity select-none"
        onClick={() => onCategoryChange('Home')}
      >
        KOLL<span className="text-[#f5c842]">Y</span>WOOD
      </div>

      <div className="hidden lg:flex items-center gap-8 text-[12px] font-bold text-[#7a7a8c] uppercase tracking-widest">
        {categories.map((cat) => (
          <div 
            key={cat}
            onClick={() => onCategoryChange(cat)}
            className={`cursor-pointer transition-colors duration-300 hover:text-[#f2efe8] ${activeCategory === cat ? 'text-[#f2efe8] relative after:absolute after:-bottom-2 after:left-0 after:right-0 after:h-0.5 after:bg-[#e8192c]' : ''}`}
          >
            {cat}
          </div>
        ))}
      </div>
      
      <div className="flex items-center gap-4 md:gap-6">
        <div className="relative group hidden sm:block">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[#5a5a6a] group-focus-within:text-[#f2efe8] transition-colors" />
          <input
            type="text"
            placeholder="Movies, stars, directors…"
            className="bg-white/5 border border-white/10 rounded-full py-2 pl-10 pr-5 text-sm w-36 md:w-56 focus:w-44 md:focus:w-72 focus:bg-white/10 focus:border-white/20 outline-none transition-all duration-300 placeholder:text-[#5a5a6a] text-[#f2efe8]"
            value={searchQuery}
            onChange={(e) => onSearch(e.target.value)}
          />
        </div>

        <div className="flex items-center gap-4 text-[#7a7a8c]">
          <Bell className="w-5 h-5 cursor-pointer hover:text-[#f2efe8] transition-colors" />
          <div className="w-8 h-8 bg-[#18181f] border border-white/10 rounded-full flex items-center justify-center overflow-hidden cursor-pointer hover:border-white/30 transition-all">
            <img src="https://api.dicebear.com/7.x/avataaars/svg?seed=Felix" alt="avatar" className="w-full h-full object-cover" />
          </div>
          <Menu className="w-6 h-6 lg:hidden cursor-pointer hover:text-[#f2efe8]" />
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
